from rest_framework import serializers
from .models import Achievements, UserAchievements

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievements
        fields = '__all__'

class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievements
        fields = ['id', 'achievement', 'earned_at']
        read_only_fields = ['id', 'earned_at']