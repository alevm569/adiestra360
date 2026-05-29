from rest_framework import serializers
from .models import Users, UserStreaks
import uuid

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Users
        fields = ['id', 'name', 'email', 'password', 'experience_level']

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        validated_data['id'] = str(uuid.uuid4())
        validated_data['password'] = make_password(validated_data['password'])
        user = Users.objects.create(**validated_data)
        UserStreaks.objects.create(id=str(uuid.uuid4()), user=user)
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['id', 'name', 'email', 'experience_level', 'created_at']

class UserStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStreaks
        fields = ['current_streak', 'longest_streak', 'updated_at']