import uuid
from django.db import models

class Users(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=150)
    password = models.CharField(max_length=255)
    experience_level = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'

class UserStreaks(models.Model):
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    user = models.OneToOneField(Users, models.CASCADE)
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_streaks'