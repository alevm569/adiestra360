import uuid
from django.db import models

from users.models import Users
from .constants import compute_sus_score


class SurveyResponses(models.Model):
    """
    Respuesta al cuestionario SUS de un usuario (una por usuario).

    Los diez ítems se guardan en columnas q1..q10 (escala 1–5) y el puntaje
    SUS (0–100) se calcula y persiste en `sus_score` al guardar, para poder
    agregarlo en las métricas sin recalcular.

    `is_simulated` marca las respuestas generadas por seed_validation, de modo
    que el panel de métricas pueda separar datos reales de sintéticos.
    """
    id = models.CharField(primary_key=True, max_length=36, default=uuid.uuid4)
    user = models.OneToOneField(Users, models.CASCADE)

    q1 = models.PositiveSmallIntegerField()
    q2 = models.PositiveSmallIntegerField()
    q3 = models.PositiveSmallIntegerField()
    q4 = models.PositiveSmallIntegerField()
    q5 = models.PositiveSmallIntegerField()
    q6 = models.PositiveSmallIntegerField()
    q7 = models.PositiveSmallIntegerField()
    q8 = models.PositiveSmallIntegerField()
    q9 = models.PositiveSmallIntegerField()
    q10 = models.PositiveSmallIntegerField()

    # Puntaje SUS derivado (0–100). Se rellena en save().
    sus_score = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    # Comentario abierto opcional (valoración cualitativa).
    comment = models.TextField(blank=True, null=True)

    is_simulated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'survey_responses'

    @property
    def answers(self):
        """Las 10 respuestas en orden q1..q10."""
        return [getattr(self, f'q{i}') for i in range(1, 11)]

    def save(self, *args, **kwargs):
        # Recalcula el puntaje SUS a partir de las respuestas actuales.
        self.sus_score = compute_sus_score(self.answers)
        super().save(*args, **kwargs)
