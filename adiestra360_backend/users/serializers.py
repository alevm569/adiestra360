from rest_framework import serializers
from .models import Users, UserStreaks
import uuid

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    # Consentimiento informado: obligatorio para registrarse.
    research_consent = serializers.BooleanField(write_only=True)

    class Meta:
        model = Users
        fields = ['id', 'name', 'email', 'password', 'experience_level',
                  'research_consent']

    def validate_research_consent(self, value):
        if not value:
            raise serializers.ValidationError(
                'Debes aceptar el uso de datos con fines de investigación para continuar.'
            )
        return value

    def create(self, validated_data):
        from django.contrib.auth.hashers import make_password
        from django.utils import timezone
        validated_data['id'] = str(uuid.uuid4())
        validated_data['password'] = make_password(validated_data['password'])
        # research_consent ya validado como True; se sella con la fecha.
        validated_data['research_consent_at'] = timezone.now()
        user = Users.objects.create(**validated_data)
        UserStreaks.objects.create(id=str(uuid.uuid4()), user=user)
        return user

class UserSerializer(serializers.ModelSerializer):
    # True si el email está en la allowlist del panel de validación
    # (VALIDATION_ADMIN_EMAILS). El front lo usa para mostrar el panel.
    is_metrics_admin = serializers.SerializerMethodField()

    class Meta:
        model = Users
        fields = ['id', 'name', 'email', 'experience_level', 'created_at',
                  'is_metrics_admin']

    def get_is_metrics_admin(self, obj):
        from validation.permissions import is_metrics_admin
        return is_metrics_admin(obj)

class UserStreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStreaks
        fields = ['current_streak', 'longest_streak', 'updated_at']