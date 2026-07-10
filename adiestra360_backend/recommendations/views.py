from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import AiRecommendations
from .serializers import AiRecommendationSerializer
from dogs.models import Dogs
from training.models import ReinforcementTypes, TrainingPlans, TrainingPlanExercises
from training_sessions.models import TrainingSessions
import uuid

SUCCESS_THRESHOLD = 0.50
MIN_SESSIONS = 3
INSIST_AFTER_SESSIONS = 2

# Categorías de ejercicios por nivel
EXERCISE_CATEGORIES = {
    'nivel_1': {
        'global': [
            'siéntate', 'échate', 'llamado', 'quédate',
            'lugar', 'obediencia_pierna', 'junto'
        ]
    },
    'nivel_2': {
        'aprendizaje': ['rastreo', 'detección de olores', 'deteccion de olores'],
        'accion': ['agility', 'trucos'],
        'disciplina': ['obediencia a la pierna sin collar', 'disciplina al frente']
    }
}

# Refuerzos primarios por categoría nivel 2
CATEGORY_REINFORCEMENT_PRIORITY = {
    'aprendizaje': ['comida'],
    'accion':      ['pelota', 'juguete'],
    'disciplina':  ['comida', 'juguete', 'caricias'],  # varía según perfil
}

# Orden general de preferencia cuando hay que sugerir un refuerzo AÚN NO
# probado y el perro no tiene ranking de encuesta guardado (respaldo final).
GLOBAL_REINFORCEMENT_PRIORITY = ['comida', 'pelota', 'juguete', 'clicker', 'caricias']

# Respaldo por energía (para perros creados antes de guardar el ranking).
ENERGY_REINFORCEMENT_PRIORITY = {
    'alto':  ['pelota', 'juguete', 'caricias', 'comida', 'clicker'],
    'medio': ['comida', 'caricias', 'pelota', 'clicker', 'juguete'],
    'bajo':  ['caricias', 'comida', 'clicker', 'pelota', 'juguete'],
}


def get_reinforcement_order(dog):
    """
    Orden en que probar refuerzos para este perro, según SU encuesta:
    1) el ranking guardado en el perro (reinforcement_priority),
    2) si no existe, el orden base por su energía,
    3) como último respaldo, el orden global.
    """
    stored = getattr(dog, 'reinforcement_priority', None)
    if stored:
        order = [p.strip() for p in stored.split(',') if p.strip()]
        if order:
            return order
    return ENERGY_REINFORCEMENT_PRIORITY.get(
        dog.energy_level, GLOBAL_REINFORCEMENT_PRIORITY
    )


def get_exercise_category(exercise_name, level_number):
    """
    Determina la categoría de un ejercicio según su nombre y nivel.
    Retorna: 'global' para nivel 1, o 'aprendizaje'/'accion'/'disciplina' para nivel 2.
    """
    name_lower = exercise_name.lower()

    if level_number == 1:
        return 'global'

    for category, exercises in EXERCISE_CATEGORIES['nivel_2'].items():
        if any(ex in name_lower for ex in exercises):
            return category

    return 'disciplina'  # fallback para nivel 2


def get_reinforcement_stats(dog_id, exercise_id=None):
    """
    Calcula tasa de éxito y tiempo promedio de respuesta
    por tipo de refuerzo usando TODAS las sesiones del perro.
    Si se pasa exercise_id, filtra solo por ese ejercicio.
    """
    sessions = TrainingSessions.objects.filter(dog_id=dog_id)
    if exercise_id:
        sessions = sessions.filter(exercise_id=exercise_id)

    stats = {}
    reinforcement_ids = sessions.values_list(
        'reinforcement_type_id', flat=True
    ).distinct()

    for ref_id in reinforcement_ids:
        ref_sessions = sessions.filter(reinforcement_type_id=ref_id)
        total = ref_sessions.count()
        if total == 0:
            continue

        successes = ref_sessions.filter(success=True).count()
        success_rate = successes / total

        times = [s.response_time for s in ref_sessions if s.response_time]
        avg_time = sum(times) / len(times) if times else None

        try:
            ref = ReinforcementTypes.objects.get(id=ref_id)
            stats[str(ref_id)] = {
                'reinforcement_id': str(ref_id),
                'reinforcement_name': ref.name,
                'total_sessions': total,
                'success_rate': round(success_rate, 3),
                'avg_response_time': round(avg_time, 1) if avg_time else None
            }
        except ReinforcementTypes.DoesNotExist:
            pass

    return stats


def score_reinforcement(stat):
    """
    Score combinado: éxito (70%) + velocidad de respuesta (30%).
    """
    success_score = stat['success_rate'] * 0.7
    if stat['avg_response_time']:
        time_score = max(0, (30 - stat['avg_response_time']) / 30) * 0.3
    else:
        time_score = 0.15
    return round(success_score + time_score, 3)


def get_current_reinforcement(dog_id):
    """
    Obtiene el refuerzo actual del plan activo del perro.
    """
    plan = TrainingPlans.objects.filter(dog_id=dog_id, active=True).first()
    if not plan:
        return None, None

    # Preferir un ejercicio ACTIVO del plan (los inactivos son de niveles
    # ya superados); como respaldo, cualquiera del plan.
    plan_exercise = (
        TrainingPlanExercises.objects.filter(training_plan=plan, active=True).first()
        or TrainingPlanExercises.objects.filter(training_plan=plan).first()
    )

    level_number = 1
    if plan.current_level:
        try:
            level_number = int(''.join(filter(str.isdigit, plan.current_level.name)))
        except (ValueError, TypeError):
            level_number = 1

    return (plan_exercise.reinforcement_type if plan_exercise else None), level_number


def sessions_since_last_recommendation(dog_id):
    """
    Cuenta sesiones desde la última recomendación.
    """
    last_rec = AiRecommendations.objects.filter(
        dog_id=dog_id
    ).order_by('-created_at').first()

    if not last_rec:
        return None

    return TrainingSessions.objects.filter(
        dog_id=dog_id,
        session_date__gt=last_rec.created_at
    ).count()


def should_analyze(dog_id):
    """
    Determina si es momento de analizar y recomendar.
    """
    total_sessions = TrainingSessions.objects.filter(dog_id=dog_id).count()

    if total_sessions < MIN_SESSIONS:
        return False, f'Se necesitan al menos {MIN_SESSIONS} sesiones para analizar.'

    current_reinforcement, level_number = get_current_reinforcement(dog_id)
    if not current_reinforcement:
        return False, 'No hay plan activo.'

    stats = get_reinforcement_stats(dog_id)
    current_stats = stats.get(str(current_reinforcement.id))

    if not current_stats:
        return False, 'Sin datos suficientes del refuerzo actual.'

    if current_stats['success_rate'] < SUCCESS_THRESHOLD:
        return True, 'Tasa de éxito por debajo del 50% con refuerzo actual.'

    # Insistir si usuario ignoró recomendación anterior
    sessions_since = sessions_since_last_recommendation(dog_id)
    if sessions_since is not None and sessions_since >= INSIST_AFTER_SESSIONS:
        last_rec = AiRecommendations.objects.filter(
            dog_id=dog_id
        ).order_by('-created_at').first()
        if last_rec and str(last_rec.recommended_strategy_id) != str(current_reinforcement.id):
            if current_stats['success_rate'] < SUCCESS_THRESHOLD:
                return True, 'El usuario no aplicó la recomendación anterior y el rendimiento no mejora.'

    return False, 'El rendimiento actual es aceptable.'


def find_best_reinforcement(stats, current_reinforcement_id, category,
                            dog_energy_level, fallback_priority=None):
    """
    Encuentra el mejor refuerzo alternativo según:
    - Nivel 1 (global): cualquier refuerzo con mejor score
    - Nivel 2: respeta prioridades por categoría y energía del perro
    Si ninguno YA PROBADO supera al actual, sugiere el mejor NO probado
    según fallback_priority (el ranking de la encuesta del perro).
    """
    current_stats = stats.get(str(current_reinforcement_id))
    current_score = score_reinforcement(current_stats) if current_stats else 0

    # Prioridad por categoría. Para 'disciplina' se ajusta según la energía
    # del perro usando una variable LOCAL, sin mutar el diccionario global
    # (que es estado compartido entre todas las requests).
    if category == 'disciplina':
        if dog_energy_level == 'alto':
            priority_names = ['juguete', 'pelota', 'caricias', 'comida']
        elif dog_energy_level == 'medio':
            priority_names = ['comida', 'caricias', 'juguete']
        else:  # bajo
            priority_names = ['caricias', 'comida', 'clicker']
    elif category == 'global':
        priority_names = GLOBAL_REINFORCEMENT_PRIORITY
    else:
        priority_names = CATEGORY_REINFORCEMENT_PRIORITY.get(category, [])

    # Obtener refuerzos candidatos según categoría
    if category == 'global':
        # Nivel 1: evaluar todos los disponibles
        candidates = [
            stat for ref_id, stat in stats.items()
            if ref_id != str(current_reinforcement_id)
        ]
    else:
        # Nivel 2: filtrar por prioridades de la categoría
        candidates = [
            stat for ref_id, stat in stats.items()
            if ref_id != str(current_reinforcement_id)
            and any(p in stat['reinforcement_name'].lower() for p in priority_names)
        ]
        # Si no hay candidatos dentro de la categoría, abrir a todos
        if not candidates:
            candidates = [
                stat for ref_id, stat in stats.items()
                if ref_id != str(current_reinforcement_id)
            ]

    best = None
    best_score = current_score

    for stat in candidates:
        s = score_reinforcement(stat)
        if s > best_score:
            best_score = s
            best = stat

    # Si ningún refuerzo YA PROBADO supera al actual, sugerir el mejor NO
    # PROBADO según el orden de prioridad. Rompe el problema del huevo y la
    # gallina: sin esto, con un solo refuerzo usado nunca se sugeriría probar
    # uno nuevo aunque el actual esté fallando.
    if best is None:
        tested_ids = set(stats.keys())
        # Orden preferido: el ranking de la encuesta del perro; si no, la
        # prioridad de la categoría.
        order = fallback_priority or priority_names
        for name in order:
            ref = (
                ReinforcementTypes.objects.filter(name__iexact=name).first()
                or ReinforcementTypes.objects.filter(name__icontains=name).first()
            )
            if (ref and str(ref.id) != str(current_reinforcement_id)
                    and str(ref.id) not in tested_ids):
                best = {
                    'reinforcement_id': str(ref.id),
                    'reinforcement_name': ref.name,
                    'total_sessions': 0,
                    'success_rate': None,
                    'avg_response_time': None,
                    'untested': True,
                }
                break

    return best


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_and_recommend(request, dog_id):
    """
    Analiza el desempeño del perro y genera recomendación
    de cambio de refuerzo si corresponde.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    should, reason = should_analyze(dog_id)
    if not should:
        return Response({
            'recommendation': None,
            'message': reason
        }, status=status.HTTP_200_OK)

    stats = get_reinforcement_stats(dog_id)
    current_reinforcement, level_number = get_current_reinforcement(dog_id)

    if not current_reinforcement:
        return Response({'error': 'No hay refuerzo activo'}, status=status.HTTP_404_NOT_FOUND)

    # Determinar categoría del ejercicio actual
    plan = TrainingPlans.objects.filter(dog_id=dog_id, active=True).first()
    current_plan_exercise = TrainingPlanExercises.objects.filter(
        training_plan=plan
    ).first()

    category = 'global'
    if current_plan_exercise and level_number == 2:
        category = get_exercise_category(
            current_plan_exercise.exercise.name,
            level_number
        )

    # Buscar mejor refuerzo (usando el ranking de la encuesta del perro)
    best = find_best_reinforcement(
        stats,
        current_reinforcement.id,
        category,
        dog.energy_level,
        get_reinforcement_order(dog)
    )

    if not best:
        return Response({
            'recommendation': None,
            'message': 'No se encontró un refuerzo alternativo mejor. Continúa con el actual.'
        }, status=status.HTTP_200_OK)

    # Construir razón legible
    current_stat = stats.get(str(current_reinforcement.id), {})
    current_success = round(current_stat.get('success_rate', 0) * 100, 1)

    if best.get('untested'):
        # Sugerencia de un refuerzo aún no probado (no hay datos para comparar).
        reason_text = (
            f"El refuerzo actual ({current_reinforcement.name}) rinde al "
            f"{current_success}% de éxito. Aún no has probado "
            f"{best['reinforcement_name']}: te recomendamos intentarlo, "
            f"suele funcionar mejor para este tipo de ejercicios."
        )
    else:
        reason_text = (
            f"Nivel {level_number} — categoría '{category}'. "
            f"El refuerzo actual ({current_reinforcement.name}) tiene "
            f"{current_success}% de éxito "
            f"con tiempo promedio de {current_stat.get('avg_response_time', 'N/A')}s. "
            f"Se recomienda {best['reinforcement_name']} con "
            f"{round(best['success_rate'] * 100, 1)}% de éxito "
            f"y tiempo promedio de {best.get('avg_response_time', 'N/A')}s."
        )

    try:
        recommended_reinforcement = ReinforcementTypes.objects.get(
            id=best['reinforcement_id']
        )
    except ReinforcementTypes.DoesNotExist:
        return Response(
            {'error': 'Refuerzo recomendado no encontrado'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Evitar duplicados: si la última recomendación ya sugiere exactamente lo
    # mismo y sigue vigente, se reutiliza en vez de crear otra igual (analyze
    # se llama tras cada sesión).
    latest = AiRecommendations.objects.filter(dog=dog).order_by('-created_at').first()
    is_duplicate = bool(
        latest
        and str(latest.previous_strategy_id) == str(current_reinforcement.id)
        and str(latest.recommended_strategy_id) == str(recommended_reinforcement.id)
    )

    if is_duplicate:
        recommendation = latest
        resp_status = status.HTTP_200_OK
    else:
        recommendation = AiRecommendations.objects.create(
            id=str(uuid.uuid4()),
            dog=dog,
            previous_strategy=current_reinforcement,
            recommended_strategy=recommended_reinforcement,
            reason=reason_text
        )
        resp_status = status.HTTP_201_CREATED

    return Response({
        'recommendation': AiRecommendationSerializer(recommendation).data,
        'level': level_number,
        'category': category,
        'current_stats': current_stat,
        'recommended_stats': best,
        'message': f'Se recomienda cambiar el refuerzo a {best["reinforcement_name"]}.'
    }, status=resp_status)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request, dog_id):
    """
    Lista el historial de recomendaciones de un perro.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    recommendations = AiRecommendations.objects.filter(
        dog=dog
    ).order_by('-created_at')

    return Response(AiRecommendationSerializer(recommendations, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_recommendation(request, dog_id):
    """
    Retorna la recomendación más reciente si aún no fue aplicada.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    current_reinforcement, _ = get_current_reinforcement(dog_id)
    last_rec = AiRecommendations.objects.filter(
        dog=dog
    ).order_by('-created_at').first()

    if not last_rec:
        return Response({'active_recommendation': None})

    if current_reinforcement and \
            str(current_reinforcement.id) == str(last_rec.recommended_strategy_id):
        return Response({
            'active_recommendation': None,
            'message': 'Recomendación ya aplicada.'
        })

    return Response({
        'active_recommendation': AiRecommendationSerializer(last_rec).data
    })