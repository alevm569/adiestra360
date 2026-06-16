from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Users, UserStreaks
from .serializers import RegisterSerializer, UserSerializer, UserStreakSerializer
import uuid

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    refresh['user_id'] = str(user.id)
    refresh['email'] = user.email
    refresh['name'] = user.name
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'error': 'Email y contraseña son requeridos'},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = Users.objects.get(email=email)
    except Users.DoesNotExist:
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.check_password(password):
        return Response(
            {'error': 'Credenciales inválidas'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    tokens = get_tokens_for_user(user)
    streak = UserStreaks.objects.filter(user=user).first()

    return Response({
        'user': UserSerializer(user).data,
        'streak': UserStreakSerializer(streak).data if streak else None,
        'tokens': tokens
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user_id = request.auth.payload.get('user_id')
    try:
        user = Users.objects.get(id=user_id)
        streak = UserStreaks.objects.filter(user=user).first()
        return Response({
            'user': UserSerializer(user).data,
            'streak': UserStreakSerializer(streak).data if streak else None,
        })
    except Users.DoesNotExist:
        return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([AllowAny])
def quiz_questions(request):
    questions = [
        {
            'id': 1,
            'category': 'dog_knowledge',
            'question': '¿Cuando llamas a tu perro por su nombre, viene hacia ti?',
            'options': ['Siempre', 'A veces', 'Casi nunca', 'Nunca'],
            'exercise_related': 'llamado'
        },
        {
            'id': 2,
            'category': 'dog_knowledge',
            'question': '¿Tu perro se sienta cuando se lo pides?',
            'options': ['Siempre', 'A veces', 'Casi nunca', 'Nunca'],
            'exercise_related': 'siéntate'
        },
        {
            'id': 3,
            'category': 'dog_knowledge',
            'question': '¿Tu perro se echa o se acuesta cuando se lo indicas?',
            'options': ['Siempre', 'A veces', 'Casi nunca', 'Nunca'],
            'exercise_related': 'échate'
        },
        {
            'id': 4,
            'category': 'dog_knowledge',
            'question': '¿Tu perro puede quedarse quieto en un lugar sin moverse por al menos 10 segundos?',
            'options': ['Siempre', 'A veces', 'Casi nunca', 'Nunca'],
            'exercise_related': 'quédate'
        },
        {
            'id': 5,
            'category': 'dog_knowledge',
            'question': '¿Tu perro camina a tu lado sin jalarte la correa?',
            'options': ['Siempre', 'A veces', 'Casi nunca', 'Nunca'],
            'exercise_related': 'obediencia_pierna'
        },
        {
            'id': 6,
            'category': 'dog_knowledge',
            'question': '¿Tu perro va a su lugar o cama cuando se lo indicas?',
            'options': ['Siempre', 'A veces', 'Casi nunca', 'Nunca'],
            'exercise_related': 'lugar'
        },
        {
            'id': 7,
            'category': 'reinforcement',
            'question': '¿Tu perro se emociona más con pelotas u objetos para jugar?',
            'options': ['Mucho', 'Algo', 'Poco', 'Nada'],
            'reinforcement_related': 'pelota'
        },
        {
            'id': 8,
            'category': 'reinforcement',
            'question': '¿Tu perro trabaja bien por golosinas o comida?',
            'options': ['Mucho', 'Algo', 'Poco', 'Nada'],
            'reinforcement_related': 'comida'
        },
        {
            'id': 9,
            'category': 'reinforcement',
            'question': '¿Tu perro responde bien a caricias y elogios verbales?',
            'options': ['Mucho', 'Algo', 'Poco', 'Nada'],
            'reinforcement_related': 'caricias'
        },
        {
            'id': 10,
            'category': 'owner_experience',
            'question': '¿Has entrenado perros antes o tomado clases de adiestramiento?',
            'options': ['Sí, tengo experiencia', 'Solo lo básico', 'Nunca pero me informo', 'Es mi primera vez'],
            'experience_related': 'experience_level'
        },
        {
            'id': 11,
            'category': 'owner_experience',
            'question': '¿Conoces la diferencia entre refuerzo positivo y corrección?',
            'options': ['Sí, lo aplico', 'Lo conozco pero no lo aplico', 'Lo he escuchado', 'No lo conozco'],
            'experience_related': 'experience_level'
        },
    ]
    return Response(questions, status=status.HTTP_200_OK)
