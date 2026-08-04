"""
Backend de correo que envía por la API HTTP de Brevo.

Desde septiembre de 2025 Render bloquea el tráfico saliente a los puertos SMTP
(25, 465 y 587) en los servicios gratuitos, así que `smtp.gmail.com` es
inalcanzable desde producción por mucho que las credenciales sean correctas.
Brevo ofrece el mismo envío sobre HTTPS (puerto 443), que sí sale.

Se habla con la API usando `urllib` de la biblioteca estándar para no añadir
dependencias nuevas al despliegue.

Cumple el contrato de `BaseEmailBackend`, así que `send_mail()` y los tests con
el backend `locmem` siguen funcionando igual.
"""
import json
import logging
import urllib.error
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

API_URL = 'https://api.brevo.com/v3/smtp/email'


def _address(value):
    """Convierte 'Nombre <correo@x>' al objeto {name, email} que pide Brevo."""
    name, email = parseaddr(value)
    address = {'email': email or value}
    if name:
        address['name'] = name
    return address


class BrevoAPIEmailBackend(BaseEmailBackend):
    """Envía cada mensaje con una petición a la API transaccional de Brevo."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'BREVO_API_KEY', '')
        self.timeout = getattr(settings, 'EMAIL_TIMEOUT', None) or 15

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        if not self.api_key:
            if self.fail_silently:
                return 0
            raise ValueError(
                'Falta BREVO_API_KEY: no se puede enviar correo por la API de Brevo.')

        return sum(1 for message in email_messages if self._send(message))

    def _payload(self, message):
        payload = {
            'sender': _address(message.from_email or settings.DEFAULT_FROM_EMAIL),
            'to': [_address(a) for a in message.to],
            'subject': message.subject,
            'textContent': message.body,
        }
        if message.cc:
            payload['cc'] = [_address(a) for a in message.cc]
        if message.bcc:
            payload['bcc'] = [_address(a) for a in message.bcc]
        if message.reply_to:
            payload['replyTo'] = _address(message.reply_to[0])

        # Si el mensaje trae versión HTML, se manda junto al texto plano.
        for content, mimetype in getattr(message, 'alternatives', []):
            if mimetype == 'text/html':
                payload['htmlContent'] = content
                break
        return payload

    def _send(self, message):
        if not message.to:
            return False

        request = urllib.request.Request(
            API_URL,
            data=json.dumps(self._payload(message)).encode('utf-8'),
            headers={
                'api-key': self.api_key,
                'accept': 'application/json',
                'content-type': 'application/json',
            },
            method='POST',
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return 200 <= response.status < 300
        except urllib.error.HTTPError as exc:
            # El cuerpo del error es lo único que distingue "API key inválida"
            # de "remitente no verificado"; sin él, depurar es adivinar.
            detail = exc.read().decode('utf-8', errors='replace')[:500]
            logger.error('Brevo rechazó el envío (HTTP %s): %s', exc.code, detail)
            if not self.fail_silently:
                raise RuntimeError(f'Brevo HTTP {exc.code}: {detail}') from exc
            return False
        except Exception:
            logger.exception('Brevo: fallo de red al enviar el correo')
            if not self.fail_silently:
                raise
            return False
