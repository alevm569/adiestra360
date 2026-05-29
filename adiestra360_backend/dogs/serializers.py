from rest_framework import serializers
from .models import Dogs
import uuid

class DogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dogs
        fields = ['id', 'name', 'breed', 'age_months', 'weight', 'energy_level', 'training_level', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        validated_data['id'] = str(uuid.uuid4())
        return super().create(validated_data)