"""
Exporta las métricas de la validación para el informe final.

- CSV: una fila por participante (real o simulado) con sus métricas clave y su
  puntaje SUS. Ideal para analizar en Excel/estadística.
- JSON: el payload agregado completo (el mismo del panel), con los segmentos
  real / simulated / combined.

Uso:
    python manage.py export_metrics --format csv  --output participantes.csv
    python manage.py export_metrics --format json --output metricas.json
    python manage.py export_metrics --format csv                 # a stdout
"""
import csv
import json
import sys

from django.core.management.base import BaseCommand

from users.models import Users, UserStreaks
from dogs.models import Dogs
from training_sessions.models import TrainingSessions
from validation.models import SurveyResponses
from validation.constants import is_simulated_email, sus_adjective
from validation.metrics import build_metrics

CSV_COLUMNS = [
    'segment', 'email', 'name', 'experience_level', 'dog_name', 'dog_breed',
    'dog_level', 'total_sessions', 'successful_sessions', 'success_rate',
    'active_days', 'current_streak', 'longest_streak', 'total_xp',
    'sus_score', 'sus_adjective', 'sus_comment',
]


class Command(BaseCommand):
    help = 'Exporta las métricas de validación a CSV (por participante) o JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--format', choices=['csv', 'json'], default='csv')
        parser.add_argument('--output', type=str, default=None,
                            help='Ruta de salida. Si se omite, escribe a stdout.')

    def handle(self, *args, **opts):
        if opts['format'] == 'json':
            payload = json.dumps(build_metrics(), ensure_ascii=False, indent=2)
            self._write(opts['output'], lambda f: f.write(payload), payload)
            return

        rows = self._participant_rows()
        if opts['output']:
            with open(opts['output'], 'w', newline='', encoding='utf-8') as f:
                self._write_csv(f, rows)
            self.stdout.write(self.style.SUCCESS(
                f'{len(rows)} participante(s) exportado(s) a {opts["output"]}.'))
        else:
            self._write_csv(sys.stdout, rows)

    def _write(self, output, to_file, payload):
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                to_file(f)
            self.stdout.write(self.style.SUCCESS(f'Exportado a {output}.'))
        else:
            self.stdout.write(payload)

    def _write_csv(self, fileobj, rows):
        writer = csv.DictWriter(fileobj, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    def _participant_rows(self):
        streaks = {s.user_id: s for s in UserStreaks.objects.all()}
        surveys = {s.user_id: s for s in SurveyResponses.objects.all()}
        rows = []
        for user in Users.objects.all():
            dog = Dogs.objects.filter(user=user).first()
            sessions = TrainingSessions.objects.filter(dog__user=user)
            total = sessions.count()
            ok = sessions.filter(success=True).count()
            active_days = (sessions.values_list('session_date__date', flat=True)
                           .distinct().count())
            streak = streaks.get(user.id)
            survey = surveys.get(user.id)
            rows.append({
                'segment': 'simulated' if is_simulated_email(user.email) else 'real',
                'email': user.email,
                'name': user.name,
                'experience_level': user.experience_level,
                'dog_name': dog.name if dog else '',
                'dog_breed': dog.breed if dog else '',
                'dog_level': dog.training_level if dog else '',
                'total_sessions': total,
                'successful_sessions': ok,
                'success_rate': round(ok / total * 100, 1) if total else '',
                'active_days': active_days,
                'current_streak': streak.current_streak if streak else '',
                'longest_streak': streak.longest_streak if streak else '',
                'total_xp': user.total_xp,
                'sus_score': float(survey.sus_score) if survey and survey.sus_score is not None else '',
                'sus_adjective': sus_adjective(float(survey.sus_score)) if survey and survey.sus_score is not None else '',
                'sus_comment': (survey.comment or '').replace('\n', ' ') if survey else '',
            })
        # Reales primero, luego por puntaje SUS descendente.
        rows.sort(key=lambda r: (r['segment'] != 'real',
                                 -(r['sus_score'] if isinstance(r['sus_score'], float) else -1)))
        return rows
