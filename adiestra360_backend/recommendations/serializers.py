from rest_framework import serializers
from .models import AiRecommendations

class AiRecommendationSerializer(serializers.ModelSerializer):
    previous_strategy_name = serializers.CharField(source='previous_strategy.name', read_only=True)
    recommended_strategy_name = serializers.CharField(source='recommended_strategy.name', read_only=True)

    class Meta:
        model = AiRecommendations
        fields = [
            'id', 'dog',
            'previous_strategy', 'previous_strategy_name',
            'recommended_strategy', 'recommended_strategy_name',
            'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']