"""
Recuperación de contraseña con un código de 6 dígitos enviado por correo.

Se eligió el código (y no un enlace) porque la app corre como PWA en el
navegador y como APK de Capacitor: un enlace abriría el navegador y sacaría al
usuario de la app instalada, mientras que un código se teclea igual en las dos.

Reglas de seguridad:
- El código se guarda hasheado y de un solo uso.
- Pedir un código invalida los anteriores del mismo usuario.
- El endpoint de solicitud responde siempre lo mismo exista o no el correo,
  para no revelar qué correos están registrados.
"""
import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.utils import timezone

from .models import PasswordResetCodes

CODE_LENGTH = 6


def _generate_code():
    """Código numérico de 6 dígitos con generador criptográfico."""
    return f'{secrets.randbelow(10 ** CODE_LENGTH):0{CODE_LENGTH}d}'


def recently_requested(user, now=None):
    """True si a este usuario ya se le mandó un código hace muy poco."""
    now = now or timezone.now()
    last = (PasswordResetCodes.objects
            .filter(user=user)
            .order_by('-created_at')
            .first())
    if last is None:
        return False
    elapsed = (now - last.created_at).total_seconds()
    return elapsed < settings.PASSWORD_RESET_RESEND_SECONDS


def create_code(user):
    """
    Invalida los códigos pendientes del usuario y crea uno nuevo.

    Devuelve (código_en_claro, registro). El registro se devuelve para poder
    borrarlo si el envío falla: si no, un correo que nunca salió dejaría al
    usuario bloqueado un minuto por el límite de reenvío.
    """
    now = timezone.now()
    PasswordResetCodes.objects.filter(user=user, used_at=None).update(used_at=now)

    code = _generate_code()
    entry = PasswordResetCodes.objects.create(
        id=str(uuid.uuid4()),
        user=user,
        code_hash=make_password(code),
        expires_at=now + timedelta(
            minutes=settings.PASSWORD_RESET_CODE_TTL_MINUTES),
    )
    return code, entry


def send_code_email(user, code):
    """
    Envía el código al correo del usuario.

    Propaga la excepción si el envío falla (`fail_silently=False`): la vista
    necesita enterarse para avisar en vez de fingir que el correo salió.
    """
    minutes = settings.PASSWORD_RESET_CODE_TTL_MINUTES
    send_mail(
        subject='Tu código para recuperar la contraseña — Adiestra360',
        message=(
            f'Hola {user.name}:\n\n'
            f'Tu código para restablecer la contraseña es:\n\n'
            f'    {code}\n\n'
            f'Escríbelo en la app junto con tu nueva contraseña. '
            f'Caduca en {minutes} minutos y solo se puede usar una vez.\n\n'
            'Si no pediste este cambio, ignora este mensaje: tu contraseña '
            'sigue siendo la misma.\n\n'
            '— Adiestra360'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def verify_code(user, code):
    """
    Comprueba el código del usuario.

    Devuelve (registro, None) si es válido, o (None, mensaje_de_error).
    Cada fallo suma un intento; agotados, el código queda inservible.
    """
    now = timezone.now()
    entry = (PasswordResetCodes.objects
             .filter(user=user, used_at=None)
             .order_by('-created_at')
             .first())

    if entry is None:
        return None, 'No hay ningún código pendiente. Solicita uno nuevo.'
    if entry.expires_at <= now:
        return None, 'El código caducó. Solicita uno nuevo.'
    if entry.attempts >= settings.PASSWORD_RESET_MAX_ATTEMPTS:
        entry.used_at = now
        entry.save(update_fields=['used_at'])
        return None, 'Demasiados intentos fallidos. Solicita un código nuevo.'

    if not check_password(code, entry.code_hash):
        entry.attempts += 1
        entry.save(update_fields=['attempts'])
        restantes = settings.PASSWORD_RESET_MAX_ATTEMPTS - entry.attempts
        if restantes <= 0:
            entry.used_at = now
            entry.save(update_fields=['used_at'])
            return None, 'Demasiados intentos fallidos. Solicita un código nuevo.'
        return None, f'Código incorrecto. Te quedan {restantes} intento(s).'

    return entry, None


def consume(entry):
    """Marca el código como usado (un solo uso)."""
    entry.used_at = timezone.now()
    entry.save(update_fields=['used_at'])
