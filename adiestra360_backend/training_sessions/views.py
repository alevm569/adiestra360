from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import TrainingSessions
from .serializers import TrainingSessionSerializer
from dogs.models import Dogs
from training.models import TrainingPlans, TrainingPlanExercises
from gamification.models import Achievements, UserAchievements
from users.models import UserStreaks
from django.utils import timezone
from datetime import timedelta
import uuid

def update_streak(user):
    """
    Actualiza la racha del usuario.
    Si entrenó ayer → racha +1.
    Si no → reset a 1.
    """
    streak, _ = UserStreaks.objects.get_or_create(
        user=user,
        defaults={'id': str(uuid.uuid4()), 'current_streak': 0, 'longest_streak': 0}
    )

    today = timezone.now().date()
    last_updated = streak.updated_at.date() if streak.updated_at else None

    # Si ya se contabilizó una sesión hoy, la racha no cambia.
    # En la primera sesión la racha está en 0, así que debe inicializarse
    # aunque la fila se haya creado hoy (en el registro del usuario).
    if last_updated == today and streak.current_streak > 0:
        return streak

    if last_updated == today - timedelta(days=1):
        # Entrenó ayer → la racha continúa
        streak.current_streak += 1
    else:
        # Primera sesión o racha rota → inicia en 1
        streak.current_streak = 1

    # Actualizar racha más larga
    if streak.current_streak > streak.longest_streak:
        streak.longest_streak = streak.current_streak

    # updated_at es auto_now: save() lo fija a "ahora" automáticamente.
    streak.save()
    return streak


def calculate_xp(success_rate, streak):
    """
    Calcula XP ganado en la sesión.
    Base: 10 XP
    Bonus por éxito: hasta 10 XP extra
    Bonus por racha: +2 XP por cada día de racha (máx 20)
    """
    base_xp = 10
    success_bonus = int(success_rate * 10)
    streak_bonus = min(streak.current_streak * 2, 20)
    return base_xp + success_bonus + streak_bonus


def check_achievements(user, dog, sessions_count, streak):
    """
    Verifica y desbloquea logros según hitos alcanzados.
    Retorna lista de logros nuevos desbloqueados.
    """
    new_achievements = []
    already_earned = UserAchievements.objects.filter(
        user=user
    ).values_list('achievement__name', flat=True)

    # Definir condiciones de logros
    conditions = [
        {
            'name': 'Primera sesión',
            'condition': sessions_count >= 1
        },
        {
            'name': 'Semana constante',
            'condition': streak.current_streak >= 7
        },
        {
            'name': 'Entrenador dedicado',
            'condition': streak.current_streak >= 30
        },
        {
            'name': '10 sesiones completadas',
            'condition': sessions_count >= 10
        },
        {
            'name': '50 sesiones completadas',
            'condition': sessions_count >= 50
        },
        {
            'name': 'Racha de 3 días',
            'condition': streak.current_streak >= 3
        },
    ]

    for cond in conditions:
        if cond['condition'] and cond['name'] not in already_earned:
            try:
                achievement = Achievements.objects.get(name=cond['name'])
                UserAchievements.objects.create(
                    id=str(uuid.uuid4()),
                    user=user,
                    achievement=achievement
                )
                # Sumar la recompensa al XP total del usuario (en memoria;
                # el caller persiste con un único user.save()).
                user.total_xp += achievement.xp_reward or 0
                new_achievements.append({
                    'name': achievement.name,
                    'description': achievement.description,
                    'xp_reward': achievement.xp_reward
                })
            except Achievements.DoesNotExist:
                pass

    return new_achievements


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_session(request, dog_id):
    """
    Registra una nueva sesión de entrenamiento.
    Actualiza racha, calcula XP y verifica logros.
    """
    user_id = request.auth.payload.get('user_id')

    try:
        from users.models import Users
        user = Users.objects.get(id=user_id)
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except (Exception) as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    data['dog'] = str(dog.id)
    data['id'] = str(uuid.uuid4())

    serializer = TrainingSessionSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session = serializer.save()

    # Calcular tasa de éxito de esta sesión
    success_rate = 1.0 if session.success else 0.0

    # Actualizar racha
    streak = update_streak(user)

    # Calcular XP de la sesión y acumularlo en el total del usuario
    xp_earned = calculate_xp(success_rate, streak)
    user.total_xp += xp_earned

    # Contar sesiones totales del perro
    sessions_count = TrainingSessions.objects.filter(dog=dog).count()

    # Verificar logros (suma su XP a user.total_xp en memoria)
    new_achievements = check_achievements(user, dog, sessions_count, streak)

    # Persistir el XP total (sesión + logros) en una sola escritura
    user.save()

    # Calcular métricas rápidas de la sesión
    recent_sessions = TrainingSessions.objects.filter(
        dog=dog,
        exercise=session.exercise
    ).order_by('-session_date')[:10]

    total = recent_sessions.count()
    successes = sum(1 for s in recent_sessions if s.success)
    success_rate_exercise = round((successes / total) * 100, 1) if total > 0 else 0

    avg_response_time = None
    times = [s.response_time for s in recent_sessions if s.response_time]
    if times:
        avg_response_time = round(sum(times) / len(times), 1)

    return Response({
        'session': TrainingSessionSerializer(session).data,
        'xp_earned': xp_earned,
        'total_xp': user.total_xp,
        'streak': {
            'current': streak.current_streak,
            'longest': streak.longest_streak
        },
        'new_achievements': new_achievements,
        'exercise_stats': {
            'success_rate': success_rate_exercise,
            'avg_response_time': avg_response_time,
            'total_sessions': total
        },
        'message': 'Sesión registrada correctamente.'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_sessions(request, dog_id):
    """
    Lista el historial de sesiones de un perro.
    Permite filtrar por ejercicio.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    exercise_id = request.query_params.get('exercise_id')
    sessions = TrainingSessions.objects.filter(dog=dog)
    if exercise_id:
        sessions = sessions.filter(exercise_id=exercise_id)

    sessions = sessions.order_by('-session_date')
    return Response(TrainingSessionSerializer(sessions, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_stats(request, dog_id):
    """
    Estadísticas completas del perro para el dashboard.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    sessions = TrainingSessions.objects.filter(dog=dog)
    total = sessions.count()

    if total == 0:
        return Response({
            'total_sessions': 0,
            'success_rate': 0,
            'avg_response_time': None,
            'by_exercise': [],
            'by_reinforcement': []
        })

    # Tasa de éxito global
    successes = sessions.filter(success=True).count()
    success_rate = round((successes / total) * 100, 1)

    # Tiempo promedio de respuesta
    times = [s.response_time for s in sessions if s.response_time]
    avg_response_time = round(sum(times) / len(times), 1) if times else None

    # Stats por ejercicio
    from training.models import Exercises
    by_exercise = []
    exercise_ids = sessions.values_list('exercise_id', flat=True).distinct()
    for ex_id in exercise_ids:
        ex_sessions = sessions.filter(exercise_id=ex_id)
        ex_total = ex_sessions.count()
        ex_success = ex_sessions.filter(success=True).count()
        ex_times = [s.response_time for s in ex_sessions if s.response_time]
        try:
            ex = Exercises.objects.get(id=ex_id)
            by_exercise.append({
                'exercise_id': str(ex_id),
                'exercise_name': ex.name,
                'total_sessions': ex_total,
                'success_rate': round((ex_success / ex_total) * 100, 1),
                'avg_response_time': round(sum(ex_times) / len(ex_times), 1) if ex_times else None
            })
        except Exercises.DoesNotExist:
            pass

    # Stats por refuerzo
    from training.models import ReinforcementTypes
    by_reinforcement = []
    reinforcement_ids = sessions.values_list('reinforcement_type_id', flat=True).distinct()
    for ref_id in reinforcement_ids:
        ref_sessions = sessions.filter(reinforcement_type_id=ref_id)
        ref_total = ref_sessions.count()
        ref_success = ref_sessions.filter(success=True).count()
        try:
            ref = ReinforcementTypes.objects.get(id=ref_id)
            by_reinforcement.append({
                'reinforcement_id': str(ref_id),
                'reinforcement_name': ref.name,
                'total_sessions': ref_total,
                'success_rate': round((ref_success / ref_total) * 100, 1)
            })
        except ReinforcementTypes.DoesNotExist:
            pass

    # Ordenar por tasa de éxito
    by_reinforcement.sort(key=lambda x: x['success_rate'], reverse=True)

    return Response({
        'total_sessions': total,
        'success_rate': success_rate,
        'avg_response_time': avg_response_time,
        'by_exercise': by_exercise,
        'by_reinforcement': by_reinforcement,
        'best_reinforcement': by_reinforcement[0]['reinforcement_name'] if by_reinforcement else None
    })