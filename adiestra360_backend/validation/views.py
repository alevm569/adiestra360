from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.models import Users
from .models import SurveyResponses
from .serializers import SurveyResponseSerializer
from .permissions import IsMetricsAdmin
from .constants import SUS_QUESTIONS, SUS_SCALE
from .metrics import build_metrics


def _current_user(request):
    user_id = request.auth.payload.get('user_id')
    return Users.objects.filter(id=user_id).first()


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def survey(request):
    """
    GET  -> preguntas SUS + escala + la respuesta previa del usuario (o null).
    POST -> crea o actualiza (upsert) la respuesta SUS del usuario actual.
    """
    user = _current_user(request)
    if user is None:
        return Response({'error': 'Usuario no encontrado'},
                        status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        existing = SurveyResponses.objects.filter(user=user).first()
        return Response({
            'questions': SUS_QUESTIONS,
            'scale': SUS_SCALE,
            'response': SurveyResponseSerializer(existing).data if existing else None,
        })

    # POST: valida y hace upsert (una respuesta por usuario).
    existing = SurveyResponses.objects.filter(user=user).first()
    serializer = SurveyResponseSerializer(instance=existing, data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # is_simulated y user no vienen del cliente: se fijan en el servidor.
    serializer.save(user=user, is_simulated=False)
    return Response(serializer.data,
                    status=status.HTTP_200_OK if existing else status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsMetricsAdmin])
def metrics(request):
    """
    Panel de validación (solo emails en VALIDATION_ADMIN_EMAILS).
    Métricas de uso, progreso, tasa de éxito y SUS, separando datos reales
    de los simulados.
    """
    return Response(build_metrics())
