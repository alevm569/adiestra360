import uuid
from django.db import models
from dogs.models import Dogs

class TrainingLevels(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'training_levels'

class Exercises(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    level = models.ForeignKey(TrainingLevels, models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    difficulty = models.IntegerField(blank=True, null=True)
    estimated_duration = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'exercises'

class ReinforcementTypes(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'reinforcement_types'

class TrainingPlans(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    dog = models.ForeignKey(Dogs, models.CASCADE)
    current_level = models.ForeignKey(
        TrainingLevels, 
        models.DO_NOTHING, 
        blank=True, 
        null=True,
        db_column='current_level'
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_plans'

class TrainingPlanExercises(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    training_plan = models.ForeignKey(TrainingPlans, models.CASCADE)
    exercise = models.ForeignKey(Exercises, models.CASCADE)
    reinforcement_type = models.ForeignKey(ReinforcementTypes, models.CASCADE)
    order_number = models.IntegerField(blank=True, null=True)
    # Marca los ejercicios que el quiz detectó como ya dominados por el perro:
    # se confirman con menos esfuerzo (1 sesión exitosa) en vez de 3.
    dominated = models.BooleanField(default=False)
    # Los ejercicios de niveles ya superados se conservan en el plan como
    # inactivos (no se eliminan ni se reemplazan).
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'training_plan_exercises'


class ExerciseTechniques(models.Model):
    """
    Cómo enseñar un ejercicio: un tutorial con pasos ordenados.

    Cada ejercicio tiene UNA técnica. Algunos pasos traen una variante
    alternativa equivalente (p. ej. "con golosina" en vez de la guía
    mecánica) con la indicación de cuándo conviene usarla.

    El contenido se carga desde training/content/<nivel>/*.json.
    """
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    exercise = models.OneToOneField(Exercises, models.CASCADE)
    # Código del módulo de la teoría, p. ej. 'OB-002'.
    code = models.CharField(max_length=20, blank=True, null=True)

    objetivo = models.TextField(blank=True, null=True)
    prerrequisito = models.TextField(blank=True, null=True)
    duracion = models.CharField(max_length=100, blank=True, null=True)
    frecuencia = models.CharField(max_length=100, blank=True, null=True)

    competencias = models.JSONField(default=list, blank=True)
    materiales = models.JSONField(default=list, blank=True)
    reglas = models.JSONField(default=list, blank=True)

    # Lista de pasos:
    # {"order", "title", "text", "image",
    #  "alternative": {"title", "text", "image", "when"} | ausente}
    steps = models.JSONField(default=list, blank=True)

    # [{"error": str, "correccion": str}]
    errores_comunes = models.JSONField(default=list, blank=True)
    criterio_avanzar = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = 'exercise_techniques'