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


def check_exercise_mastered(dog_id, exercise_id):
    """
    Verifica si un ejercicio está dominado:
    últimas 3 sesiones con >= 80% de éxito.
    """
    sessions = TrainingSessions.objects.filter(
        dog_id=dog_id,
        exercise_id=exercise_id
    ).order_by('-session_date')[:UNLOCK_SESSION_COUNT]

    if sessions.count() < UNLOCK_SESSION_COUNT:
        return False

    success_count = sum(1 for s in sessions if s.success)
    return (success_count / UNLOCK_SESSION_COUNT) >= UNLOCK_SUCCESS_THRESHOLD


def check_level_completed(dog_id, plan):
    """
    Verifica si todos los ejercicios del nivel actual están dominados.
    """
    plan_exercises = TrainingPlanExercises.objects.filter(training_plan=plan)
    for pe in plan_exercises:
        if not check_exercise_mastered(dog_id, pe.exercise_id):
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

    # Obtener el refuerzo actual del plan
    current_reinforcement = TrainingPlanExercises.objects.filter(
        training_plan=plan
    ).first()

    reinforcement = current_reinforcement.reinforcement_type if current_reinforcement else \
        ReinforcementTypes.objects.first()

    # Agregar al plan
    order = TrainingPlanExercises.objects.filter(training_plan=plan).count() + 1
    TrainingPlanExercises.objects.create(
        id=str(uuid.uuid4()),
        training_plan=plan,
        exercise=next_exercise,
        reinforcement_type=reinforcement,
        order_number=order
    )
    return next_exercise


def upgrade_to_next_level(dog, plan):
    """
    Sube el plan al siguiente nivel si todos los ejercicios
    del nivel actual están dominados.
    Retorna (upgraded: bool, new_level_name: str)
    """
    current_level = plan.current_level
    next_level = TrainingLevels.objects.filter(
        id__gt=current_level.id
    ).order_by('id').first()

    if not next_level:
        return False, None

    # Actualizar plan al nuevo nivel
    plan.current_level = next_level
    plan.save()

    # Agregar primeros 2 ejercicios del nuevo nivel
    new_exercises = Exercises.objects.filter(
        level=next_level
    ).order_by('difficulty')[:2]

    reinforcement = TrainingPlanExercises.objects.filter(
        training_plan=plan
    ).first()
    reinforcement_type = reinforcement.reinforcement_type if reinforcement else \
        ReinforcementTypes.objects.first()

    for i, exercise in enumerate(new_exercises):
        TrainingPlanExercises.objects.create(
            id=str(uuid.uuid4()),
            training_plan=plan,
            exercise=exercise,
            reinforcement_type=reinforcement_type,
            order_number=i + 1
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

    # Verificar si el ejercicio fue dominado
    if check_exercise_mastered(dog.id, exercise_id):
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