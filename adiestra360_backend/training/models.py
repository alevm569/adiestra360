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
    current_level = models.ForeignKey(TrainingLevels, models.DO_NOTHING, blank=True, null=True)
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

    class Meta:
        db_table = 'training_plan_exercises'