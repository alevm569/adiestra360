import uuid
from django.db import models
from dogs.models import Dogs
from training.models import ReinforcementTypes

class AiRecommendations(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    dog = models.ForeignKey(Dogs, models.CASCADE)
    previous_strategy = models.ForeignKey(ReinforcementTypes, models.DO_NOTHING, related_name='previous_recommendations')
    recommended_strategy = models.ForeignKey(ReinforcementTypes, models.DO_NOTHING, related_name='recommended_recommendations')
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_recommendations'