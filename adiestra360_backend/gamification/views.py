from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Achievements, UserAchievements
from .serializers import AchievementSerializer, UserAchievementSerializer
from users.models import Users, UserStreaks
import uuid

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_achievements(request):
    """
    Lista todos los logros disponibles en el sistema.
    """
    achievements = Achievements.objects.all().order_by('xp_reward')
    return Response(AchievementSerializer(achievements, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_achievements(request):
    """
    Lista los logros desbloqueados por el usuario autenticado.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    earned = UserAchievements.objects.filter(
        user=user
    ).order_by('-earned_at').select_related('achievement')

    # Todos los logros disponibles
    all_achievements = Achievements.objects.all()
    earned_ids = earned.values_list('achievement_id', flat=True)

    return Response({
        'earned': UserAchievementSerializer(earned, many=True).data,
        'pending': AchievementSerializer(
            all_achievements.exclude(id__in=earned_ids), many=True
        ).data,
        'total_earned': earned.count(),
        'total_available': all_achievements.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    """
    Retorna XP total, nivel del usuario y racha actual.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # XP total acumulado de logros
    earned = UserAchievements.objects.filter(
        user=user
    ).select_related('achievement')
    total_xp = sum(ua.achievement.xp_reward for ua in earned if ua.achievement.xp_reward)

    # Nivel del usuario basado en XP
    # 0-99 XP → Principiante, 100-299 → Intermedio, 300+ → Avanzado
    if total_xp < 100:
        user_level = 'Principiante'
        next_level_xp = 100
    elif total_xp < 300:
        user_level = 'Intermedio'
        next_level_xp = 300
    else:
        user_level = 'Avanzado'
        next_level_xp = None

    # Racha
    streak = UserStreaks.objects.filter(user=user).first()

    return Response({
        'total_xp': total_xp,
        'user_level': user_level,
        'next_level_xp': next_level_xp,
        'xp_to_next_level': (next_level_xp - total_xp) if next_level_xp else 0,
        'streak': {
            'current': streak.current_streak if streak else 0,
            'longest': streak.longest_streak if streak else 0,
        },
        'achievements_earned': earned.count(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard(request, dog_id):
    """
    Endpoint unificado del dashboard.
    Agrega toda la información que necesita la pantalla principal.
    """
    from dogs.models import Dogs
    from training.models import TrainingPlans, TrainingPlanExercises
    from training.serializers import TrainingPlanSerializer
    from training_sessions.models import TrainingSessions
    from recommendations.models import AiRecommendations
    from recommendations.serializers import AiRecommendationSerializer
    from recommendations.views import get_current_reinforcement

    user_id = request.auth.payload.get('user_id')

    try:
        user = Users.objects.get(id=user_id)
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except (Users.DoesNotExist, Dogs.DoesNotExist):
        return Response({'error': 'Usuario o perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # ── Plan activo ──
    plan = TrainingPlans.objects.filter(dog=dog, active=True).first()
    plan_data = TrainingPlanSerializer(plan).data if plan else None

    # ── Estadísticas de sesiones ──
    sessions = TrainingSessions.objects.filter(dog=dog)
    total_sessions = sessions.count()
    successes = sessions.filter(success=True).count()
    success_rate = round((successes / total_sessions) * 100, 1) if total_sessions > 0 else 0

    times = [s.response_time for s in sessions if s.response_time]
    avg_response_time = round(sum(times) / len(times), 1) if times else None

    # Última sesión
    last_session = sessions.order_by('-session_date').first()

    # ── Progreso por ejercicio ──
    from training.models import Exercises
    exercise_progress = []
    if plan:
        plan_exercises = TrainingPlanExercises.objects.filter(
            training_plan=plan
        ).select_related('exercise')
        for pe in plan_exercises:
            ex_sessions = sessions.filter(exercise=pe.exercise)
            ex_total = ex_sessions.count()
            ex_success = ex_sessions.filter(success=True).count()
            exercise_progress.append({
                'exercise_id': str(pe.exercise.id),
                'exercise_name': pe.exercise.name,
                'total_sessions': ex_total,
                'success_rate': round((ex_success / ex_total) * 100, 1) if ex_total > 0 else 0,
                'mastered': ex_total >= 3 and (ex_success / ex_total) >= 0.8 if ex_total >= 3 else False
            })

    # ── Racha ──
    streak = UserStreaks.objects.filter(user=user).first()

    # ── XP y nivel ──
    earned = UserAchievements.objects.filter(user=user).select_related('achievement')
    total_xp = sum(ua.achievement.xp_reward for ua in earned if ua.achievement.xp_reward)
    if total_xp < 100:
        user_level = 'Principiante'
    elif total_xp < 300:
        user_level = 'Intermedio'
    else:
        user_level = 'Avanzado'

    # ── Logros recientes ──
    recent_achievements = UserAchievements.objects.filter(
        user=user
    ).order_by('-earned_at')[:3].select_related('achievement')

    # ── Recomendación IA activa ──
    current_reinforcement, _ = get_current_reinforcement(str(dog.id))
    last_rec = AiRecommendations.objects.filter(dog=dog).order_by('-created_at').first()
    active_recommendation = None
    if last_rec and current_reinforcement:
        if str(current_reinforcement.id) != str(last_rec.recommended_strategy_id):
            active_recommendation = AiRecommendationSerializer(last_rec).data

    return Response({
        'dog': {
            'id': str(dog.id),
            'name': dog.name,
            'breed': dog.breed,
            'training_level': dog.training_level,
            'energy_level': dog.energy_level,
        },
        'plan': plan_data,
        'stats': {
            'total_sessions': total_sessions,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'last_session': str(last_session.session_date) if last_session else None,
        },
        'exercise_progress': exercise_progress,
        'gamification': {
            'total_xp': total_xp,
            'user_level': user_level,
            'streak': {
                'current': streak.current_streak if streak else 0,
                'longest': streak.longest_streak if streak else 0,
            },
            'recent_achievements': [
                {
                    'name': ua.achievement.name,
                    'xp_reward': ua.achievement.xp_reward,
                    'earned_at': str(ua.earned_at)
                } for ua in recent_achievements
            ]
        },
        'active_recommendation': active_recommendation,
    })