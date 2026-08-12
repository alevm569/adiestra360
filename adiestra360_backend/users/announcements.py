"""
Aviso por correo a todos los usuarios de la app.

Se escribió para anunciar el cierre de la recolección de datos de la tesis
(23 de agosto), pero el asunto y el cuerpo se pueden sobrescribir para
cualquier otro aviso puntual.

Dos decisiones que conviene no revertir sin pensarlo:

- Se envía un correo por destinatario, nunca una lista en `to` ni en copia
  oculta. Con copia oculta un fallo del proveedor puede exponer la lista
  completa de correos de los participantes, que es justo lo que el
  consentimiento informado promete no hacer.
- Un envío que falla no aborta el resto: con ~15 participantes, un correo
  rebotado no puede dejar sin avisar a los demás. Los fallos se devuelven
  para poder reintentarlos a mano.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail

from users.models import Users
from validation.constants import is_simulated_email

logger = logging.getLogger(__name__)

DEADLINE = '23 de agosto de 2026'

SUBJECT = f'Adiestra360 estará disponible hasta el {DEADLINE}'

BODY = """Hola {name}:

Te escribo para contarte que estoy cerrando la recogida de datos de mi tesis \
de máster, para la que Adiestra360 es el proyecto central.

Podrás seguir usando la app con total normalidad hasta el {deadline}. A partir \
de esa fecha necesito congelar los datos para analizarlos y preparar la \
defensa, así que estos días son los últimos que cuentan.

Si te apetece echarme una mano en la recta final, hay dos cosas que me \
ayudarían muchísimo:

1) Sigue registrando tus sesiones de entrenamiento. Cada sesión que anotes \
suma a las métricas de uso (rachas, días activos, tasa de éxito) que son la \
base de los resultados.

2) Rellena el cuestionario de usabilidad, si aún no lo has hecho. Son 10 \
preguntas y se responde en menos de dos minutos. Lo tienes en la app, en \
Perfil → Cuestionario de usabilidad.{survey_link}

Gracias de verdad por haber probado Adiestra360 y por el tiempo que le has \
dedicado. Sin gente usándola de verdad esta tesis no existiría.

Un saludo,
— Adiestra360
"""


def _survey_link():
    """Enlace directo a la encuesta, solo si se configuró la URL pública."""
    base = getattr(settings, 'APP_PUBLIC_URL', '')
    if not base:
        return ''
    return f'\n\nEnlace directo: {base.rstrip("/")}/validacion/encuesta'


def recipients(include_simulated=False):
    """Usuarios a los que se enviaría el aviso, en orden de registro."""
    users = Users.objects.all().order_by('created_at')
    if include_simulated:
        return list(users)
    return [u for u in users if not is_simulated_email(u.email)]


def render_body(user, template=None):
    return (template or BODY).format(
        name=user.name,
        deadline=DEADLINE,
        survey_link=_survey_link(),
    )


def send_to(user, subject=None, template=None):
    """Envía el aviso a un usuario. Devuelve None si fue bien, o el error."""
    try:
        send_mail(
            subject=subject or SUBJECT,
            message=render_body(user, template),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return None
    except Exception as exc:
        logger.error('Aviso no enviado a %s: %s', user.email, exc)
        return f'{type(exc).__name__}: {exc}'


def broadcast(include_simulated=False, subject=None, template=None):
    """
    Envía el aviso a todos los destinatarios.

    Devuelve (enviados, fallidos), donde `fallidos` es una lista de
    (email, motivo) para poder reintentar solo esos.
    """
    enviados, fallidos = [], []
    for user in recipients(include_simulated):
        error = send_to(user, subject, template)
        if error is None:
            enviados.append(user.email)
        else:
            fallidos.append((user.email, error))
    return enviados, fallidos
