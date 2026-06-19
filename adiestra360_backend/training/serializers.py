from rest_framework import serializers
from .models import TrainingLevels, Exercises, ReinforcementTypes, TrainingPlans, TrainingPlanExercises
import uuid

class TrainingLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingLevels
        fields = '__all__'

class ExerciseSerializer(serializers.ModelSerializer):
    level_name = serializers.CharField(source='level.name', read_only=True)

    class Meta:
        model = Exercises
        fields = ['id', 'name', 'description', 'difficulty', 'estimated_duration', 'level', 'level_name']

class ReinforcementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReinforcementTypes
        fields = '__all__'

class TrainingPlanExerciseSerializer(serializers.ModelSerializer):
    exercise = ExerciseSerializer(read_only=True)
    reinforcement_type = ReinforcementTypeSerializer(read_only=True)

    class Meta:
        model = TrainingPlanExercises
        fields = ['id', 'exercise', 'reinforcement_type', 'order_number', 'dominated', 'active']

class TrainingPlanSerializer(serializers.ModelSerializer):
    exercises = TrainingPlanExerciseSerializer(
        source='trainingplanexercises_set', many=True, read_only=True
    )
    current_level_name = serializers.CharField(source='current_level.name', read_only=True)

    class Meta:
        model = TrainingPlans
        fields = ['id', 'dog', 'current_level', 'current_level_name', 'active', 'created_at', 'exercises']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['id'] = str(uuid.uuid4())
        return super().create(validated_data)