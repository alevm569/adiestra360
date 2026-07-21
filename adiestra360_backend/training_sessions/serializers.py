from rest_framework import serializers
from .models import TrainingSessions
import uuid

class TrainingSessionSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    reinforcement_name = serializers.CharField(source='reinforcement_type.name', read_only=True)

    class Meta:
        model = TrainingSessions
        fields = [
            'id', 'dog', 'exercise', 'exercise_name',
            'reinforcement_type', 'reinforcement_name',
            'response_time', 'duration_seconds', 'repetitions',
            'success', 'criteria_met', 'criteria_total', 'notes', 'session_date'
        ]
        read_only_fields = ['id', 'session_date']

    def create(self, validated_data):
        validated_data['id'] = str(uuid.uuid4())
        return super().create(validated_data)