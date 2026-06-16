from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Dogs
from .serializers import DogSerializer
from users.models import Users
from training.models import (
    TrainingLevels, Exercises, ReinforcementTypes,
    TrainingPlans, TrainingPlanExercises
)
import uuid

# Mapa de ejercicios Nivel 1 en orden de dificultad
NIVEL1_EJERCICIOS = [
    'siéntate',
    'échate',
    'llamado',
    'quédate',
    'lugar',
    'obediencia_pierna',
]

# Mapa de respuestas a puntaje
SCORE_MAP = {
    'Siempre': 2,
    'A veces': 1,
    'Casi nunca': 0,
    'Nunca': 0,
}

REINFORCEMENT_MAP = {
    'Mucho': 3,
    'Algo': 2,
    'Poco': 1,
    'Nada': 0,
}

EXPERIENCE_MAP = {
    'Sí, tengo experiencia': 'avanzado',
    'Solo lo básico': 'intermedio',
    'Nunca pero me informo': 'principiante',
    'Es mi primera vez': 'principiante',
}

def calculate_initial_level(quiz_answers, energy_level):
    """
    Determina el nivel inicial del perro basado en las respuestas del quiz.
    Retorna: training_level (1 o 2), ejercicios_dominados (lista de nombres)
    """
    dog_answers = {a['exercise_related']: a['answer']
                   for a in quiz_answers
                   if a.get('exercise_related')}

    dominated = []
    for ejercicio in NIVEL1_EJERCICIOS:
        answer = dog_answers.get(ejercicio, 'Nunca')
        if SCORE_MAP.get(answer, 0) == 2:
            dominated.append(ejercicio)

    # Si domina todos los del nivel 1 → nivel 2, sino nivel 1
    training_level = 2 if len(dominated) == len(NIVEL1_EJERCICIOS) else 1
    return training_level, dominated

def calculate_initial_reinforcement(quiz_answers, energy_level):
    """
    Determina el refuerzo inicial según energía y respuestas del quiz.
    """
    # Prioridad base por energía
    priority = {
        'alto':  ['pelota', 'juguete', 'caricias', 'comida', 'clicker'],
        'medio': ['comida', 'caricias', 'pelota', 'clicker', 'juguete'],
        'bajo':  ['caricias', 'comida', 'clicker', 'pelota', 'juguete'],
    }.get(energy_level, ['comida', 'caricias', 'pelota', 'clicker', 'juguete'])

    # Ajustar según respuestas del quiz de refuerzo
    scores = {}
    for a in quiz_answers:
        if a.get('reinforcement_related'):
            scores[a['reinforcement_related']] = REINFORCEMENT_MAP.get(a['answer'], 0)

    # Si algún refuerzo tiene score alto, sube en la prioridad
    if scores:
        priority = sorted(
            priority,
            key=lambda r: scores.get(r, 0),
            reverse=True
        )

    return priority[0]  # refuerzo principal

def calculate_experience_level(quiz_answers):
    """
    Determina el nivel de experiencia del dueño.
    """
    for a in quiz_answers:
        if a.get('experience_related') == 'experience_level':
            return EXPERIENCE_MAP.get(a['answer'], 'principiante')
    return 'principiante'

def generate_training_plan(dog, training_level, dominated_exercises, initial_reinforcement):
    """
    Genera el plan de entrenamiento inicial con 2 ejercicios activos.
    Los ejercicios ya dominados se marcan como completados.
    """
    try:
        level = TrainingLevels.objects.get(name__icontains=f'Nivel {training_level}')
    except TrainingLevels.DoesNotExist:
        # Fallback al primer nivel disponible
        level = TrainingLevels.objects.first()
        if not level:
            return None

    # Obtener tipo de refuerzo
    try:
        reinforcement = ReinforcementTypes.objects.get(
            name__icontains=initial_reinforcement
        )
    except ReinforcementTypes.DoesNotExist:
        reinforcement = ReinforcementTypes.objects.first()
        if not reinforcement:
            return None

    # Crear plan
    plan = TrainingPlans.objects.create(
        id=str(uuid.uuid4()),
        dog=dog,
        current_level=level,
        active=True
    )

    # Obtener ejercicios del nivel ordenados por dificultad
    exercises = Exercises.objects.filter(level=level).order_by('difficulty')

    # Agregar ejercicios al plan
    # Los dominados van primero, luego los activos (máx 2 no dominados)
    active_count = 0
    for i, exercise in enumerate(exercises):
        is_dominated = any(
            d.lower() in exercise.name.lower()
            for d in dominated_exercises
        )
        # Solo agregar hasta 2 ejercicios no dominados como activos
        if not is_dominated and active_count < 2:
            TrainingPlanExercises.objects.create(
                id=str(uuid.uuid4()),
                training_plan=plan,
                exercise=exercise,
                reinforcement_type=reinforcement,
                order_number=i + 1
            )
            active_count += 1
        elif is_dominated:
            TrainingPlanExercises.objects.create(
                id=str(uuid.uuid4()),
                training_plan=plan,
                exercise=exercise,
                reinforcement_type=reinforcement,
                order_number=i + 1
            )

    return plan


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_dog_profile(request):
    """
    Crea el perfil del perro procesando el quiz y generando el plan.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        user = Users.objects.get(id=user_id)
    except Users.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    # Datos del perro
    dog_data = request.data.get('dog', {})
    quiz_answers = request.data.get('quiz_answers', [])

    if not dog_data:
        return Response({'error': 'Datos del perro requeridos'}, status=status.HTTP_400_BAD_REQUEST)
    if not quiz_answers:
        return Response({'error': 'Respuestas del quiz requeridas'}, status=status.HTTP_400_BAD_REQUEST)

    energy_level = dog_data.get('energy_level', 'medio')

    # Procesar quiz
    training_level, dominated = calculate_initial_level(quiz_answers, energy_level)
    initial_reinforcement = calculate_initial_reinforcement(quiz_answers, energy_level)
    experience_level = calculate_experience_level(quiz_answers)

    # Actualizar experience_level del usuario
    user.experience_level = experience_level
    user.save()

    # Crear perro
    dog_data['id'] = str(uuid.uuid4())
    dog_data['user'] = str(user.id)
    dog_data['training_level'] = training_level

    serializer = DogSerializer(data=dog_data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    dog = serializer.save()

    # Generar plan
    plan = generate_training_plan(dog, training_level, dominated, initial_reinforcement)
    if not plan:
        return Response(
            {'error': 'No se pudo generar el plan. Verifica que existan niveles y ejercicios en la base de datos.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response({
        'dog': DogSerializer(dog).data,
        'training_level': training_level,
        'experience_level': experience_level,
        'initial_reinforcement': initial_reinforcement,
        'dominated_exercises': dominated,
        'plan_id': str(plan.id),
        'message': f'Perfil creado. Plan de entrenamiento Nivel {training_level} generado con {initial_reinforcement} como refuerzo principal.'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_dogs(request):
    """
    Lista todos los perros del usuario autenticado.
    """
    user_id = request.auth.payload.get('user_id')
    dogs = Dogs.objects.filter(user_id=user_id)
    return Response(DogSerializer(dogs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dog_detail(request, dog_id):
    """
    Detalle de un perro específico.
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
        return Response(DogSerializer(dog).data)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_dog(request, dog_id):
    """
    Actualiza datos básicos del perro (no el nivel de entrenamiento).
    """
    user_id = request.auth.payload.get('user_id')
    try:
        dog = Dogs.objects.get(id=dog_id, user_id=user_id)
    except Dogs.DoesNotExist:
        return Response({'error': 'Perro no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    serializer = DogSerializer(dog, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)