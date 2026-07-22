import os

from rest_framework.permissions import BasePermission


def metrics_admin_emails():
    """
    Allowlist de emails con acceso al panel de métricas, leída de la variable
    de entorno VALIDATION_ADMIN_EMAILS (separada por comas). En minúsculas.

    El modelo Users no tiene is_staff/is_superuser (extiende AbstractBaseUser),
    por eso la administración de la validación se gobierna por esta lista.
    """
    raw = os.getenv('VALIDATION_ADMIN_EMAILS', '')
    return {e.strip().lower() for e in raw.split(',') if e.strip()}


def is_metrics_admin(user):
    """True si el email del usuario está en la allowlist de métricas."""
    email = getattr(user, 'email', None)
    return bool(email) and email.lower() in metrics_admin_emails()


class IsMetricsAdmin(BasePermission):
    """Permite el acceso solo a los emails de VALIDATION_ADMIN_EMAILS."""
    message = 'No tienes acceso al panel de validación.'

    def has_permission(self, request, view):
        return bool(request.user) and is_metrics_admin(request.user)
