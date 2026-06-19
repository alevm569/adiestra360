"""
Utilidades compartidas para los tests de todas las apps.

Construyen los datos mínimos (catálogo, usuario autenticado, perro,
plan y sesiones) directamente por el ORM, para que cada test de
endpoint sea independiente del flujo del quiz.
"""
import uuid

from rest_framework.test import APIClient

from users.models import Users, UserStreaks
from dogs.models import Dogs
from training.models import (
    TrainingLevels, Exercises, ReinforcementTypes,
    TrainingPlans, TrainingPlanExercises,
)
from training_sessions.models import TrainingSessions
from gamification.models import Achievements, UserAchievements


def create_catalog():
    """
    Crea niveles (1 y 2), ejercicios de ambos niveles y refuerzos.

    Retorna un dict con acceso cómodo:
        catalog['levels']['lvl1'|'lvl2']
        catalog['exercises']['sientate'|...]
        catalog['reinforcements']['comida'|...]
    """
    lvl1 = TrainingLevels.objects.create(
        id='lvl-001', name='Nivel 1', description='Obediencia básica'
    )
    lvl2 = TrainingLevels.objects.create(
        id='lvl-002', name='Nivel 2', description='Obediencia intermedia'
    )

    exercises = {}
    lvl1_exercises = [
        ('ex-001', 'sientate', 'Siéntate', 1),
        ('ex-002', 'echate', 'Échate', 2),
        ('ex-003', 'llamado', 'Llamado', 3),
    ]
    lvl2_exercises = [
        ('ex-101', 'rastreo', 'Rastreo', 1),
        ('ex-102', 'agility', 'Agility', 2),
        ('ex-103', 'disciplina', 'Disciplina al frente', 3),
    ]
    for ex_id, key, name, diff in lvl1_exercises:
        exercises[key] = Exercises.objects.create(
            id=ex_id, level=lvl1, name=name,
            description='desc', difficulty=diff, estimated_duration=10,
        )
    for ex_id, key, name, diff in lvl2_exercises:
        exercises[key] = Exercises.objects.create(
            id=ex_id, level=lvl2, name=name,
            description='desc', difficulty=diff, estimated_duration=10,
        )

    reinforcements = {}
    refs = [
        ('ref-001', 'comida', 'Comida'),
        ('ref-002', 'pelota', 'Pelota'),
        ('ref-003', 'caricias', 'Caricias'),
        ('ref-004', 'clicker', 'Clicker'),
        ('ref-005', 'juguete', 'Juguete'),
    ]
    for ref_id, key, name in refs:
        reinforcements[key] = ReinforcementTypes.objects.create(id=ref_id, name=name)

    return {
        'levels': {'lvl1': lvl1, 'lvl2': lvl2},
        'exercises': exercises,
        'reinforcements': reinforcements,
    }


def create_achievements():
    """
    Crea los logros que el motor de sesiones intenta desbloquear.
    Retorna un dict por nombre.
    """
    data = [
        ('Primera sesión', 'Completaste tu primera sesión', 10),
        ('Racha de 3 días', '3 días seguidos entrenando', 20),
        ('Semana constante', '7 días seguidos', 50),
        ('10 sesiones completadas', '10 sesiones', 40),
        ('50 sesiones completadas', '50 sesiones', 100),
        ('Entrenador dedicado', '30 días seguidos', 150),
    ]
    achievements = {}
    for name, desc, xp in data:
        achievements[name] = Achievements.objects.create(
            id=str(uuid.uuid4()), name=name, description=desc, xp_reward=xp
        )
    return achievements


def make_user(email='owner@test.com', name='Owner',
              password='test1234', experience_level='principiante'):
    """Crea un usuario con su racha asociada."""
    user = Users.objects.create_user(
        email=email, name=name, password=password,
        experience_level=experience_level,
    )
    UserStreaks.objects.get_or_create(
        user=user,
        defaults={'id': str(uuid.uuid4()), 'current_streak': 0, 'longest_streak': 0},
    )
    return user


def auth_client(user):
    """Devuelve un APIClient autenticado como el usuario dado."""
    from users.views import get_tokens_for_user
    client = APIClient()
    tokens = get_tokens_for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return client


def create_dog(user, name='Luna', breed='Mestizo',
               energy_level='medio', training_level=1):
    return Dogs.objects.create(
        id=str(uuid.uuid4()), user=user, name=name, breed=breed,
        age_months=12, weight=10.5, energy_level=energy_level,
        training_level=training_level,
    )


def create_plan(dog, level, exercise_reinforcement_pairs, active=True):
    """
    Crea un plan activo con sus ejercicios.

    exercise_reinforcement_pairs: lista de tuplas (Exercises, ReinforcementTypes).
    Retorna (plan, [TrainingPlanExercises...]).
    """
    plan = TrainingPlans.objects.create(
        id=str(uuid.uuid4()), dog=dog, current_level=level, active=active
    )
    plan_exercises = []
    for i, (exercise, reinforcement) in enumerate(exercise_reinforcement_pairs, start=1):
        plan_exercises.append(
            TrainingPlanExercises.objects.create(
                id=str(uuid.uuid4()), training_plan=plan,
                exercise=exercise, reinforcement_type=reinforcement,
                order_number=i,
            )
        )
    return plan, plan_exercises


def create_session(dog, exercise, reinforcement, success=True,
                   response_time=5, duration_seconds=60, repetitions=5):
    """Crea una sesión de entrenamiento por el ORM (session_date = ahora)."""
    return TrainingSessions.objects.create(
        id=str(uuid.uuid4()), dog=dog, exercise=exercise,
        reinforcement_type=reinforcement, success=success,
        response_time=response_time, duration_seconds=duration_seconds,
        repetitions=repetitions,
    )
