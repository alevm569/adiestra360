import uuid
from django.db import models
from users.models import Users

class Dogs(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    user = models.ForeignKey(Users, models.CASCADE)
    name = models.CharField(max_length=100)
    breed = models.CharField(max_length=100, blank=True, null=True)
    age_months = models.IntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    energy_level = models.CharField(max_length=20, blank=True, null=True)
    training_level = models.IntegerField(blank=True, null=True)
    # Ranking de refuerzos según la encuesta (coma-separado, del mejor al peor).
    # Se usa para sugerir el siguiente refuerzo cuando el actual no funciona.
    reinforcement_priority = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'dogs'