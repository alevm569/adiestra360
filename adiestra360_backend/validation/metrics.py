"""
Agregación de métricas de la fase de validación.

Todo se deriva de los datos existentes (sesiones, planes, rachas, XP) más las
respuestas SUS. Cada métrica se calcula por segmento: `real` (los usuarios de
la prueba), `simulated` (los generados por seed_validation) y `combined`.

La separación real/simulado se hace por el dominio del email (ver constants).
"""
from statistics import mean, median

from django.db.models import Avg

from users.models import Users, UserStreaks
from dogs.models import Dogs
from training.models import Exercises, TrainingPlanExercises
from training_sessions.models import TrainingSessions
from .models import SurveyResponses
from .constants import (
    SUS_QUESTIONS, SUS_ITEM_COUNT, sus_adjective, is_simulated_email,
)


def _round(value, ndigits=1):
    return round(value, ndigits) if value is not None else None


def _segment_user_ids():
    """Devuelve (real_ids, simulated_ids) según el dominio del email."""
    real, simulated = [], []
    for uid, email in Users.objects.values_list('id', 'email'):
        (simulated if is_simulated_email(email) else real).append(uid)
    return real, simulated


def _usage_metrics(user_ids):
    """Uso y progreso de un conjunto de usuarios."""
    dogs = Dogs.objects.filter(user_id__in=user_ids)
    dog_ids = list(dogs.values_list('id', flat=True))
    sessions = TrainingSessions.objects.filter(dog_id__in=dog_ids)

    total_sessions = sessions.count()
    successes = sessions.filter(success=True).count()
    success_rate = _round(successes / total_sessions * 100) if total_sessions else 0.0

    # Cumplimiento del checklist de criterios (solo sesiones que lo registraron).
    ratios = [
        s.criteria_met / s.criteria_total
        for s in sessions.exclude(criteria_total=None).exclude(criteria_total=0)
        if s.criteria_met is not None
    ]
    criteria_completion = _round(mean(ratios) * 100) if ratios else None

    # Días activos por usuario (fechas distintas con al menos una sesión).
    day_rows = (
        sessions.values_list('dog__user_id', 'session_date__date')
        .distinct()
    )
    days_by_user = {}
    for uid, _day in day_rows:
        days_by_user[uid] = days_by_user.get(uid, 0) + 1
    active_days_values = list(days_by_user.values())

    streaks = UserStreaks.objects.filter(user_id__in=user_ids)
    xp_values = list(Users.objects.filter(id__in=user_ids)
                     .values_list('total_xp', flat=True))

    # Progreso: distribución de nivel de los perros y ejercicios dominados.
    level_dist = {}
    for lvl in dogs.values_list('training_level', flat=True):
        key = str(lvl) if lvl is not None else 'sin_nivel'
        level_dist[key] = level_dist.get(key, 0) + 1

    mastered = TrainingPlanExercises.objects.filter(
        training_plan__dog_id__in=dog_ids, dominated=True
    ).count()

    n_users = len(user_ids)
    return {
        'users': n_users,
        'dogs': len(dog_ids),
        'total_sessions': total_sessions,
        'success_rate': success_rate,
        'criteria_completion_rate': criteria_completion,
        'avg_sessions_per_user': _round(total_sessions / n_users) if n_users else 0.0,
        'avg_active_days': _round(mean(active_days_values)) if active_days_values else 0.0,
        'avg_total_xp': _round(mean(xp_values)) if xp_values else 0.0,
        'avg_current_streak': _round(
            streaks.aggregate(v=Avg('current_streak'))['v']),
        'avg_longest_streak': _round(
            streaks.aggregate(v=Avg('longest_streak'))['v']),
        'mastered_exercises': mastered,
        'dog_level_distribution': level_dist,
    }


def _by_exercise(user_ids):
    """Tasa de éxito por ejercicio para un conjunto de usuarios."""
    dog_ids = list(Dogs.objects.filter(user_id__in=user_ids)
                   .values_list('id', flat=True))
    sessions = TrainingSessions.objects.filter(dog_id__in=dog_ids)
    names = dict(Exercises.objects.values_list('id', 'name'))

    rows = []
    ex_ids = sessions.values_list('exercise_id', flat=True).distinct()
    for ex_id in ex_ids:
        ex_sessions = sessions.filter(exercise_id=ex_id)
        total = ex_sessions.count()
        ok = ex_sessions.filter(success=True).count()
        rows.append({
            'exercise_id': str(ex_id),
            'exercise_name': names.get(ex_id, '—'),
            'total_sessions': total,
            'success_rate': _round(ok / total * 100) if total else 0.0,
        })
    rows.sort(key=lambda r: r['total_sessions'], reverse=True)
    return rows


def _sus_summary(user_ids):
    """Resumen del cuestionario SUS para un conjunto de usuarios."""
    responses = list(SurveyResponses.objects.filter(user_id__in=user_ids))
    n = len(responses)
    if n == 0:
        return {
            'n': 0, 'mean': None, 'median': None, 'min': None, 'max': None,
            'adjective': None, 'above_industry_avg_pct': None,
            'per_item_mean': [], 'distribution': {},
        }

    scores = [float(r.sus_score) for r in responses]
    mean_score = _round(mean(scores))

    # Distribución en tramos de la escala de adjetivos.
    buckets = {'Deficiente': 0, 'Pobre': 0, 'Aceptable': 0, 'Bueno': 0, 'Excelente': 0}
    for s in scores:
        buckets[sus_adjective(s)] += 1

    per_item = []
    for i, question in enumerate(SUS_QUESTIONS, start=1):
        values = [getattr(r, f'q{i}') for r in responses]
        per_item.append({
            'id': question['id'],
            'positive': question['positive'],
            'mean': _round(mean(values), 2),
        })

    above = sum(1 for s in scores if s >= 68)  # 68 ≈ media de la industria
    return {
        'n': n,
        'mean': mean_score,
        'median': _round(median(scores)),
        'min': _round(min(scores)),
        'max': _round(max(scores)),
        'adjective': sus_adjective(mean_score),
        'above_industry_avg_pct': _round(above / n * 100),
        'per_item_mean': per_item,
        'distribution': buckets,
    }


def _segment(user_ids):
    return {
        'usage': _usage_metrics(user_ids),
        'sus': _sus_summary(user_ids),
        'by_exercise': _by_exercise(user_ids),
    }


def build_metrics():
    """Construye el payload completo de métricas de validación."""
    real_ids, sim_ids = _segment_user_ids()
    all_ids = real_ids + sim_ids
    return {
        'sus_item_count': SUS_ITEM_COUNT,
        'sus_questions': SUS_QUESTIONS,
        'counts': {
            'real_users': len(real_ids),
            'simulated_users': len(sim_ids),
            'total_users': len(all_ids),
        },
        'real': _segment(real_ids),
        'simulated': _segment(sim_ids),
        'combined': _segment(all_ids),
    }
