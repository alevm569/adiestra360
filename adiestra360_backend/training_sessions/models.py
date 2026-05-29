import uuid
from django.db import models
from dogs.models import Dogs
from training.models import Exercises, ReinforcementTypes

class TrainingSessions(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    dog = models.ForeignKey(Dogs, models.CASCADE)
    exercise = models.ForeignKey(Exercises, models.CASCADE)
    reinforcement_type = models.ForeignKey(ReinforcementTypes, models.CASCADE)
    response_time = models.IntegerField(blank=True, null=True)
    duration_seconds = models.IntegerField(blank=True, null=True)
    repetitions = models.IntegerField(blank=True, null=True)
    success = models.BooleanField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    session_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'training_sessions'