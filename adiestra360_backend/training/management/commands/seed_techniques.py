"""
Carga las técnicas (cómo enseñar cada ejercicio) desde los JSON curados
en training/content/<nivel>/*.json — la fuente de verdad de la teoría.

Uso:  python manage.py seed_techniques
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand
from training.models import Exercises, ExerciseTechniques

CONTENT_DIR = Path(__file__).resolve().parents[2] / 'content'

# Campos del JSON que se copian tal cual al modelo.
FIELDS = [
    'objetivo', 'prerrequisito', 'duracion', 'frecuencia',
    'competencias', 'materiales', 'reglas', 'steps',
    'errores_comunes', 'criterio_avanzar',
]


class Command(BaseCommand):
    help = 'Carga las técnicas desde los JSON de training/content/.'

    def find_exercise(self, name):
        """Busca el ejercicio por nombre exacto y, si no, por coincidencia."""
        return (
            Exercises.objects.filter(name__iexact=name).first()
            or Exercises.objects.filter(name__icontains=name).first()
        )

    def handle(self, *args, **options):
        if not CONTENT_DIR.exists():
            self.stdout.write(self.style.ERROR(f'No existe {CONTENT_DIR}'))
            return

        files = sorted(CONTENT_DIR.glob('*/*.json'))
        if not files:
            self.stdout.write(self.style.WARNING('No hay JSON de contenido.'))
            return

        loaded = 0
        for path in files:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)

            name = data.get('exercise')
            exercise = self.find_exercise(name) if name else None
            if not exercise:
                self.stdout.write(self.style.WARNING(
                    f"{path.name}: ejercicio '{name}' no está en la BD, se omite."
                ))
                continue

            defaults = {k: data.get(k) for k in FIELDS if k in data}
            # El código del módulo viene como "id" en el JSON (p. ej. OB-002).
            defaults['code'] = data.get('code') or data.get('id')
            ExerciseTechniques.objects.update_or_create(
                exercise=exercise, defaults=defaults
            )
            steps = len(data.get('steps', []))
            alts = sum(1 for s in data.get('steps', []) if s.get('alternative'))
            self.stdout.write(self.style.SUCCESS(
                f"{data.get('code', '?')} {exercise.name}: {steps} pasos "
                f"({alts} con variante)"
            ))
            loaded += 1

        self.stdout.write(self.style.SUCCESS(f'\n{loaded} técnica(s) cargada(s).'))
