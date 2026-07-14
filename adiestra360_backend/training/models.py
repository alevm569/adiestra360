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


class TrainingMethods(models.Model):
    """
    Métodos globales de enseñanza (p. ej. 'Señuelo', 'Moldeado').
    Se recomienda uno u otro según la motivación (energía) del perro.
    """
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    key = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    # Niveles de motivación (energy_level) para los que se recomienda este
    # método, separados por coma. P. ej. 'alto' o 'medio,bajo'.
    motivation_levels = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'training_methods'


class ExerciseTechniques(models.Model):
    """
    Cómo enseñar un ejercicio con un método concreto: los pasos.
    Un ejercicio tiene una técnica por cada método global.
    """
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    exercise = models.ForeignKey(Exercises, models.CASCADE)
    method = models.ForeignKey(TrainingMethods, models.CASCADE)
    # Pasos de la técnica: lista de objetos {"text": str, "image": url|null}.
    # Cada paso puede llevar una imagen (las del PDF).
    steps = models.JSONField(default=list, blank=True)
    tips = models.TextField(blank=True, null=True)
    materials = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'exercise_techniques'
        unique_together = ('exercise', 'method')