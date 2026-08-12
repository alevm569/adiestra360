"""
Envía el aviso de cierre de la recogida de datos a los usuarios de la app.

Esta es la vía para lanzarlo desde una máquina con acceso a la base de datos.
En Render gratis no hay shell, así que desde producción se dispara el mismo
código con `POST /api/validation/announcement/` (ver `users.announcements`).

Uso:
    python manage.py send_announcement --dry-run   # lista destinatarios y texto
    python manage.py send_announcement             # envía de verdad
"""
from django.conf import settings
from django.core.management.base import BaseCommand

from users import announcements


class Command(BaseCommand):
    help = 'Envía el aviso por correo a los usuarios reales de la app.'

    def add_arguments(self, parser):
        parser.add_argument('--subject', default=None,
                            help='Asunto alternativo.')
        parser.add_argument('--include-simulated', action='store_true',
                            help='Incluye los usuarios simulados de las pruebas.')
        parser.add_argument('--dry-run', action='store_true',
                            help='No envía nada: lista destinatarios y el texto.')

    def handle(self, *args, **opts):
        destinatarios = announcements.recipients(opts['include_simulated'])
        if not destinatarios:
            self.stdout.write(self.style.WARNING('No hay destinatarios.'))
            return

        self.stdout.write(f'Backend:   {settings.EMAIL_BACKEND}')
        self.stdout.write(f'Remitente: {settings.DEFAULT_FROM_EMAIL}')
        self.stdout.write(f'Asunto:    {opts["subject"] or announcements.SUBJECT}')
        self.stdout.write(f'Destinatarios: {len(destinatarios)}\n')

        if opts['dry_run']:
            for user in destinatarios:
                self.stdout.write(f'  - {user.name} <{user.email}>')
            self.stdout.write('\n--- Vista previa ---')
            self.stdout.write(announcements.render_body(destinatarios[0]))
            self.stdout.write(self.style.WARNING('Dry-run: no se envió nada.'))
            return

        enviados, fallidos = announcements.broadcast(
            include_simulated=opts['include_simulated'],
            subject=opts['subject'],
        )
        for email in enviados:
            self.stdout.write(f'  OK    {email}')
        for email, motivo in fallidos:
            self.stdout.write(self.style.ERROR(f'  FALLO {email}: {motivo}'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'{len(enviados)}/{len(destinatarios)} correos enviados.'))
