from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import (
    TrainingLevels, Exercises, ReinforcementTypes,
    TrainingPlans, TrainingPlanExercises
)
from .serializers import (
    TrainingLevelSerializer, ExerciseSerializer,
    ReinforcementTypeSerializer, TrainingPlanSerializer,
    TrainingPlanExerciseSerializer
)
from dogs.models import Dogs
from training_sessions.models import TrainingSessions
import uuid

UNLOCK_SUCCESS_THRESHOLD = 0.80  # 80% de éxito mínimo
UNLOCK_SESSION_COUNT = 3         # mínimo 3 sesiones para evaluar


def check_exercise_mastered(dog_id, exercise_id, dominated=False):
    """
    Verifica si un ejercicio está dominado.

    - Ejercicio normal: últimas 3 sesiones con >= 80% de éxito.
    - Ejercicio marcado como dominado en el quiz: basta 1 sesión exitosa
      para confirmarlo, porque el perro ya lo sabe y debería costarle poco.
      Si la última sesión falla (le costó esfuerzo), se evalúa con la regla
      normal: en realidad debe repasarlo.
    """
    if dominated:
        last_session = TrainingSessions.objects.filter(
            dog_id=dog_id,
            exercise_id=exercise_id
        ).order_by('-session_date').first()
        if last_session and last_session.success:
            return True
        # Falló o aún no hay sesión → se evalúa con la regla estándar.

    sessions = TrainingSessions.objects.filter(
        dog_id=dog_id,
        exercise_id=exercise_id
    ).order_by('-session_date')[:UNLOCK_SESSION_COUNT]

    if sessions.count() < UNLOCK_SESSION_COUNT:
        return False

    success_count = sum(1 for s in sessions if s.success)
    return (success_count / UNLOCK_SESSION_COUNT) >= UNLOCK_SUCCESS_THRESHOLD


def get_level_number(level):
    """
    Extrae el número de un nivel a partir de su nombre (p.ej. 'Nivel 2' → 2).
    Retorna None si no se puede determinar.
    """
    if not level:
        return None
    try:
        return int(''.join(filter(str.isdigit, level.name)))
    except (ValueError, TypeError):
        return None


def check_level_completed(dog_id, plan):
    """
    Verifica si todos los ejercicios ACTIVOS del nivel actual están dominados.
    Los ejercicios de niveles anteriores (inactivos) no se evalúan.
    """
    plan_exercises = TrainingPlanExercises.objects.filter(
        training_plan=plan, active=True
    )
    for pe in plan_exercises:
        if not check_exercise_mastered(dog_id, pe.exercise_id, dominated=pe.dominated):
            return False
    return True


def unlock_next_exercise(dog, plan):
    """
    Desbloquea el siguiente ejercicio si el actual fue dominado.
    Retorna el ejercicio desbloqueado o None.
    """
    # Ejercicios ya en el plan
    current_exercise_ids = TrainingPlanExercises.objects.filter(
        training_plan=plan
    ).values_list('exercise_id', flat=True)

    # Siguiente ejercicio del nivel no agregado aún
    next_exercise = Exercises.objects.filter(
        level=plan.current_level
    ).exclude(
        id__in=current_exercise_ids
    ).order_by('difficulty').first()

    if not next_exercise:
        return None

    # Refuerzo: el de un ejercicio activo del plan, o cualquiera disponible.
    current_reinforcement = (
        TrainingPlanExercises.objects.filter(training_plan=plan, active=True).first()
        or TrainingPlanExercises.objects.filter(training_plan=plan).first()
    )
    reinforcement = current_reinforcement.reinforcement_type if current_reinforcement else \
        ReinforcementTypes.objects.first()

    # Continuar la numeración desde el último order_number del plan.
    last = TrainingPlanExercises.objects.filter(
        training_plan=plan
    ).order_by('-order_number').first()
    last_order = last.order_number if last and last.order_number else 0

    TrainingPlanExercises.objects.create(
        id=str(uuid.uuid4()),
        training_plan=plan,
        exercise=next_exercise,
        reinforcement_type=reinforcement,
        order_number=last_order + 1,
        active=True,
        dominated=False
    )
    return next_exercise


def upgrade_to_next_level(dog, plan):
    """
    Sube el plan al siguiente nivel si todos los ejercicios
    del nivel actual están dominados.
    Retorna (upgraded: bool, new_level_name: str)
    """
    current_level = plan.current_level
    current_number = get_level_number(current_level)
    if current_number is None:
        return False, None

    # El "siguiente nivel" se determina por el número del nombre (Nivel N+1),
    # no por el id, que es un UUID sin orden semántico.
    next_level = next(
        (lvl for lvl in TrainingLevels.objects.all()
         if get_level_number(lvl) == current_number + 1),
        None
    )

    if not next_level:
        return False, None

    # Refuerzo de referencia (tomado del plan actual, antes de inactivar).
    reinforcement = TrainingPlanExercises.objects.filter(
        training_plan=plan
    ).first()
    reinforcement_type = reinforcement.reinforcement_type if reinforcement else \
        ReinforcementTypes.objects.first()

    # Continuar la numeración desde el último order_number existente.
    last = TrainingPlanExercises.objects.filter(
        training_plan=plan
    ).order_by('-order_number').first()
    last_order = last.order_number if last and last.order_number else 0

    # Actualizar plan al nuevo nivel
    plan.current_level = next_level
    plan.save()

    # Los ejercicios del nivel anterior se conservan pero quedan inactivos
    # (no se eliminan ni se reemplazan).
    TrainingPlanExercises.objects.filter(training_plan=plan).update(active=False)

    # Agregar primeros 2 ejercicios del nuevo nivel como activos.
    new_exercises = Exercises.objects.filter(
        level=next_level
    ).order_by('difficulty')[:2]

    for i, exercise in enumerate(new_exercises):
        TrainingPlanExercises.objects.create(
            id=str(uuid.uuid4()),
            training_plan=plan,
            exercise=exercise,
            reinforcement_type=reinforcement_type,
            order_number=last_order + 1 + i,
            active=True,
            dominated=False
        )

    return True, next_level.name


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_levels(request):
    levels = TrainingLevels.objects.all()
    return Response(TrainingLevelSerializer(levels, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_exercises(request):
    level_id = request.query_params.get('level_id')
    exercises = Exercises.objects.filter(level_id=level_id) if level_id \
        else Exercises.objects.all()
    return Response(ExerciseSerializer(exercises, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_reinforcements(request):
    reinforcements = ReinforcementTypes.objects.all()
    return Response(ReinforcementTypeSerializer(reinforcements, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_plan(request, dog_id):
    """
    Retorna el plan activo del perro con sus ejercicios.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    plan = TrainingPlans.objects.filter(dog=dog, active=True).first()
    if not plan:
        return Response({'error': 'No hay plan activo'}, status=status.HTTP_404_NOT_FOUND)

    return Response(TrainingPlanSerializer(plan).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def evaluate_progress(request, dog_id):
    """
    Evalúa el progreso del perro después de una sesión.
    Desbloquea ejercicios o sube de nivel si corresponde.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    plan = TrainingPlans.objects.filter(dog=dog, active=True).first()
    if not plan:
        return Response({'error': 'No hay plan activo'}, status=status.HTTP_404_NOT_FOUND)

    exercise_id = request.data.get('exercise_id')
    if not exercise_id:
        return Response({'error': 'exercise_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    response_data = {
        'exercise_mastered': False,
        'next_exercise_unlocked': None,
        'level_upgraded': False,
        'new_level': None,
        'message': ''
    }

    # Saber si el ejercicio evaluado fue marcado como dominado en el quiz
    # (se confirma con menos esfuerzo).
    evaluated_pe = TrainingPlanExercises.objects.filter(
        training_plan=plan, exercise_id=exercise_id
    ).first()
    is_dominated = evaluated_pe.dominated if evaluated_pe else False

    # Verificar si el ejercicio fue dominado
    if check_exercise_mastered(dog.id, exercise_id, dominated=is_dominated):
        response_data['exercise_mastered'] = True

        # Verificar si completó todo el nivel
        if check_level_completed(dog.id, plan):
            upgraded, new_level_name = upgrade_to_next_level(dog, plan)
            if upgraded:
                response_data['level_upgraded'] = True
                response_data['new_level'] = new_level_name
                response_data['message'] = (
                    f'¡Felicidades! {dog.name} ha completado el nivel actual. '
                    f'El {new_level_name} está ahora disponible.'
                )
            else:
                response_data['message'] = '¡Has completado todos los niveles disponibles!'
        else:
            # Desbloquear siguiente ejercicio
            next_ex = unlock_next_exercise(dog, plan)
            if next_ex:
                response_data['next_exercise_unlocked'] = ExerciseSerializer(next_ex).data
                response_data['message'] = (
                    f'¡Ejercicio dominado! Has desbloqueado: {next_ex.name}'
                )
            else:
                response_data['message'] = '¡Ejercicio dominado! Sigue practicando los demás.'
    else:
        response_data['message'] = 'Sigue entrenando, aún no alcanzas el 80% de éxito en 3 sesiones.'

    return Response(response_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_exercise_reinforcement(request, dog_id, plan_exercise_id):
    """
    Actualiza el tipo de refuerzo de un ejercicio específico del plan.
    Se usa cuando la IA recomienda cambiar la estrategia.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    try:
        plan_exercise = TrainingPlanExercises.objects.get(
            id=plan_exercise_id,
            training_plan__dog=dog
        )
    except TrainingPlanExercises.DoesNotExist:
        return Response({'error': 'Ejercicio no encontrado en el plan'}, status=status.HTTP_404_NOT_FOUND)

    reinforcement_id = request.data.get('reinforcement_type_id')
    if not reinforcement_id:
        return Response({'error': 'reinforcement_type_id requerido'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        reinforcement = ReinforcementTypes.objects.get(id=reinforcement_id)
    except ReinforcementTypes.DoesNotExist:
        return Response({'error': 'Tipo de refuerzo no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    plan_exercise.reinforcement_type = reinforcement
    plan_exercise.save()

    return Response({
        'message': f'Refuerzo actualizado a {reinforcement.name}',
        'plan_exercise': TrainingPlanExerciseSerializer(plan_exercise).data
    })