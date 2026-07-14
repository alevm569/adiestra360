from django.core.management.base import BaseCommand
from training.models import Exercises, TrainingMethods, ExerciseTechniques


# Los dos métodos globales. La asignación de motivación es una propuesta
# inicial: ajústala con el contenido del PDF de técnicas.
METHODS = [
    {
        'key': 'senuelo',
        'name': 'Señuelo',
        'description': (
            'Guías al perro con un premio (comida o juguete) para provocar la '
            'postura y lo recompensas al lograrla.'
        ),
        'motivation_levels': 'medio,bajo',  # necesita guía directa
    },
    {
        'key': 'moldeado',
        'name': 'Moldeado',
        'description': (
            'Premias aproximaciones sucesivas a la conducta hasta lograrla; '
            'el perro va ofreciendo comportamientos.'
        ),
        'motivation_levels': 'alto',  # el perro propone conductas
    },
]

# Pasos de EJEMPLO (placeholder). Reemplázalos con el contenido del PDF.
SAMPLE_TECHNIQUES = {
    'siéntate': {
        'senuelo': {
            'steps': [
                'Sostén un premio cerca de la nariz del perro.',
                'Sube el premio despacio por encima de su cabeza.',
                'Al seguir el premio con la mirada, su cola baja y se sienta.',
                'En cuanto se siente, di "Siéntate" y dale el premio.',
                'Repite 5–8 veces por sesión.',
            ],
            'tips': 'No subas el premio muy alto o saltará en vez de sentarse.',
            'materials': 'Premios pequeños y blandos.',
        },
        'moldeado': {
            'steps': [
                'Observa al perro y espera a que empiece a sentarse solo.',
                'Marca (clicker o "sí") el momento en que dobla las patas.',
                'Recompensa cada aproximación al sentado.',
                'Cuando ya se siente completo, añade la palabra "Siéntate".',
            ],
            'tips': 'Ten paciencia: premia los intentos, no solo el resultado final.',
            'materials': 'Clicker (opcional) y premios.',
        },
    },
    'llamado': {
        'senuelo': {
            'steps': [
                'Ponte a poca distancia con un premio visible.',
                'Di el nombre + "Ven" en tono alegre y muestra el premio.',
                'Cuando llegue, recompensa y felicítalo mucho.',
                'Aumenta la distancia poco a poco.',
            ],
            'tips': 'Nunca llames al perro para algo que le desagrade.',
            'materials': 'Premios de alto valor y correa larga.',
        },
        'moldeado': {
            'steps': [
                'Premia cualquier acercamiento espontáneo hacia ti.',
                'Marca el instante en que se mueve en tu dirección.',
                'Sube el criterio: premia solo cuando llega hasta ti.',
                'Añade la señal "Ven" cuando el patrón sea sólido.',
            ],
            'tips': 'Refuerza mucho al inicio para crear el hábito.',
            'materials': 'Premios y un espacio seguro.',
        },
    },
}


class Command(BaseCommand):
    help = 'Crea los métodos de enseñanza y técnicas de EJEMPLO (placeholder).'

    def handle(self, *args, **options):
        methods = {}
        for m in METHODS:
            obj, _ = TrainingMethods.objects.update_or_create(
                key=m['key'],
                defaults={
                    'name': m['name'],
                    'description': m['description'],
                    'motivation_levels': m['motivation_levels'],
                },
            )
            methods[m['key']] = obj
            self.stdout.write(f'Método: {obj.name} ({obj.motivation_levels})')

        for ex_name, per_method in SAMPLE_TECHNIQUES.items():
            exercise = Exercises.objects.filter(name__icontains=ex_name).first()
            if not exercise:
                self.stdout.write(self.style.WARNING(
                    f"Ejercicio '{ex_name}' no encontrado en la BD, se omite."
                ))
                continue
            for method_key, content in per_method.items():
                ExerciseTechniques.objects.update_or_create(
                    exercise=exercise,
                    method=methods[method_key],
                    defaults={
                        # Cada paso: {text, image}. La imagen del PDF va aquí
                        # (por ahora None en los ejemplos).
                        'steps': [{'text': s, 'image': None} for s in content['steps']],
                        'tips': content.get('tips'),
                        'materials': content.get('materials'),
                    },
                )
            self.stdout.write(self.style.SUCCESS(f"Técnicas de '{exercise.name}' cargadas."))

        self.stdout.write(self.style.SUCCESS('Seed de técnicas completado.'))
