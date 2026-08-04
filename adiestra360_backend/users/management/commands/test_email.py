"""
Prueba el envío de correo sin pasar por la app.

Sirve para separar dos problemas que desde la pantalla de recuperación se ven
igual: "las credenciales del correo están mal" y "el flujo de recuperación
falla". Imprime qué transporte está activo y luego intenta un envío real.

    python manage.py test_email tucorreo@gmail.com
"""
from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Envía un correo de prueba para verificar la configuración.'

    def add_arguments(self, parser):
        parser.add_argument('to', help='Destinatario del correo de prueba.')

    def handle(self, *args, **opts):
        destino = opts['to']

        self.stdout.write(f'Backend:   {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Remitente: {settings.DEFAULT_FROM_EMAIL}')
        if 'Brevo' in settings.EMAIL_BACKEND:
            clave = settings.BREVO_API_KEY
            self.stdout.write(f'API key:   {clave[:9]}…{clave[-4:]} '
                              f'({len(clave)} caracteres)')
            # Los dos errores típicos se ven en la forma de la clave, sin
            # necesidad de llamar a la API.
            if clave.startswith('xsmtpsib-'):
                self.stdout.write(self.style.ERROR(
                    'Esa es la clave SMTP, no la API key. La API v3 la rechaza '
                    'con "Key not found": genera una en la pestaña API Keys.'))
            elif not clave.startswith('xkeysib-'):
                self.stdout.write(self.style.WARNING(
                    'Una API key v3 de Brevo empieza por "xkeysib-".'))
            if '…' in clave or '...' in clave or '*' in clave:
                self.stdout.write(self.style.ERROR(
                    'La clave está enmascarada: se copió del panel después de '
                    'cerrar el modal. Hay que generar una nueva.'))
            self.stdout.write(
                'Recuerda: el remitente de arriba debe estar verificado en Brevo.')
        elif 'smtp' in settings.EMAIL_BACKEND:
            self.stdout.write(
                f'Servidor:  {settings.EMAIL_HOST}:{settings.EMAIL_PORT} '
                f'(usuario {settings.EMAIL_HOST_USER or "—"})')
            self.stdout.write(self.style.WARNING(
                'SMTP no funciona en Render gratis (puertos bloqueados); '
                'en local sí.'))
        elif 'console' in settings.EMAIL_BACKEND:
            self.stdout.write(self.style.WARNING(
                'Sin credenciales de correo: se imprimirá abajo en vez de enviarse.'))
        self.stdout.write('')

        try:
            enviados = send_mail(
                subject='Correo de prueba — Adiestra360',
                message='Si estás leyendo esto, el envío de correo funciona.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[destino],
                fail_silently=False,
            )
        except Exception as exc:
            # El mensaje del proveedor es lo único que dice si el problema es
            # de credenciales, de puerto bloqueado o de remitente no verificado.
            self.stderr.write(self.style.ERROR(
                f'Falló el envío: {type(exc).__name__}: {exc}'))
            return

        if enviados:
            self.stdout.write(self.style.SUCCESS(f'Correo enviado a {destino}.'))
        else:
            self.stderr.write(self.style.ERROR(
                'El proveedor aceptó la petición pero no envió nada.'))
