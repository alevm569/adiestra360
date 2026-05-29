import uuid
from django.db import models
from users.models import Users

class Achievements(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    xp_reward = models.IntegerField(default=0)

    class Meta:
        db_table = 'achievements'

class UserAchievements(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    user = models.ForeignKey(Users, models.CASCADE)
    achievement = models.ForeignKey(Achievements, models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_achievements'