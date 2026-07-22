from rest_framework import serializers

from .models import SurveyResponses
from .constants import sus_adjective

_ITEM_FIELDS = [f'q{i}' for i in range(1, 11)]


class SurveyResponseSerializer(serializers.ModelSerializer):
    """Lee/escribe una respuesta SUS. El puntaje se calcula en el modelo."""
    sus_adjective = serializers.SerializerMethodField()

    class Meta:
        model = SurveyResponses
        fields = ['id'] + _ITEM_FIELDS + [
            'sus_score', 'sus_adjective', 'comment',
            'is_simulated', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'sus_score', 'is_simulated',
                            'created_at', 'updated_at']

    def get_sus_adjective(self, obj):
        return sus_adjective(float(obj.sus_score)) if obj.sus_score is not None else None

    def validate(self, attrs):
        # En creación exigimos las 10 respuestas; en actualización parcial no.
        if not self.partial:
            missing = [f for f in _ITEM_FIELDS if attrs.get(f) is None]
            if missing:
                raise serializers.ValidationError(
                    'Debes responder las 10 preguntas del cuestionario.'
                )
        for f in _ITEM_FIELDS:
            value = attrs.get(f)
            if value is not None and not 1 <= value <= 5:
                raise serializers.ValidationError(
                    {f: 'La respuesta debe estar entre 1 y 5.'}
                )
        return attrs
