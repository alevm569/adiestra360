"""
Genera datos SIMULADOS para complementar a los ~15 usuarios reales de la
prueba de validación: usuarios sintéticos con su perro, plan, historial de
sesiones (distribuido en el tiempo), racha, XP, logros y respuesta SUS.

Los usuarios simulados usan un email @sim.adiestra360.local (ver constants),
así el panel de métricas los separa de los reales. Es reproducible: con el
mismo --seed produce siempre el mismo dataset.

Requiere que el catálogo real ya exista (niveles, ejercicios, refuerzos):
corre primero las migraciones/carga de datos de la app.

Uso:
    python manage.py seed_validation                 # 15 usuarios, seed 42
    python manage.py seed_validation --users 20 --days 45
    python manage.py seed_validation --clear          # borra los previos y regenera
"""
import random
import uuid
from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from users.models import Users, UserStreaks
from dogs.models import Dogs
from training.models import (
    TrainingLevels, Exercises, ReinforcementTypes,
    TrainingPlans, TrainingPlanExercises,
)
from training_sessions.models import TrainingSessions
from gamification.models import Achievements, UserAchievements
from validation.models import SurveyResponses
from validation.constants import (
    SIMULATED_EMAIL_DOMAIN, is_simulated_email, compute_sus_score,
)

BREEDS = [
    'Mestizo', 'Labrador', 'Golden Retriever', 'Pastor Alemán', 'Bulldog',
    'Beagle', 'Poodle', 'Chihuahua', 'Border Collie', 'Boxer', 'Schnauzer',
]
ENERGY = ['bajo', 'medio', 'alto']
EXPERIENCE = ['principiante', 'intermedio', 'avanzado']
FIRST_NAMES = [
    'Ana', 'Luis', 'María', 'Carlos', 'Sofía', 'Diego', 'Valentina', 'Andrés',
    'Camila', 'Jorge', 'Daniela', 'Pablo', 'Lucía', 'Mateo', 'Paula', 'Bruno',
    'Elena', 'Ricardo', 'Gabriela', 'Tomás',
]
DOG_NAMES = [
    'Luna', 'Rocky', 'Max', 'Bella', 'Toby', 'Nina', 'Zeus', 'Coco', 'Simba',
    'Kira', 'Thor', 'Maya', 'Bruno', 'Lola', 'Duke', 'Canela', 'Rex', 'Frida',
]


class Command(BaseCommand):
    help = 'Genera usuarios/sesiones/encuestas SIMULADOS para la validación.'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=15,
                            help='Cuántos usuarios simulados crear (def. 15).')
        parser.add_argument('--seed', type=int, default=42,
                            help='Semilla RNG para reproducibilidad (def. 42).')
        parser.add_argument('--days', type=int, default=30,
                            help='Ventana en días para repartir las sesiones (def. 30).')
        parser.add_argument('--password', type=str, default='sim1234',
                            help='Contraseña de los usuarios simulados.')
        parser.add_argument('--clear', action='store_true',
                            help='Borra los datos simulados previos antes de generar.')

    # --- utilidades ----------------------------------------------------------
    def _load_catalog(self):
        levels = list(TrainingLevels.objects.order_by('name'))
        reinforcements = list(ReinforcementTypes.objects.all())
        by_level = {
            lvl.id: list(Exercises.objects.filter(level=lvl).order_by('difficulty'))
            for lvl in levels
        }
        return levels, reinforcements, by_level

    def _clear_simulated(self):
        sim_ids = [
            uid for uid, email in Users.objects.values_list('id', 'email')
            if is_simulated_email(email)
        ]
        if not sim_ids:
            self.stdout.write('No había usuarios simulados que borrar.')
            return
        # El borrado en cascada arrastra perros, planes, sesiones, rachas,
        # logros y respuestas SUS de esos usuarios.
        Users.objects.filter(id__in=sim_ids).delete()
        self.stdout.write(self.style.WARNING(
            f'Borrados {len(sim_ids)} usuario(s) simulado(s) y sus datos.'))

    # --- generación ----------------------------------------------------------
    @transaction.atomic
    def handle(self, *args, **opts):
        rng = random.Random(opts['seed'])
        now = timezone.now()
        window = max(1, opts['days'])
        pwd = make_password(opts['password'])

        if opts['clear']:
            self._clear_simulated()

        levels, reinforcements, by_level = self._load_catalog()
        if not levels or not reinforcements or not any(by_level.values()):
            self.stdout.write(self.style.ERROR(
                'Falta el catálogo (niveles/ejercicios/refuerzos). Corre primero '
                'las migraciones y la carga de datos base de la app.'))
            return

        achievements = {a.name: a for a in Achievements.objects.all()}
        num_levels = len(levels)
        created = 0

        for i in range(1, opts['users'] + 1):
            email = f'sim-{i:03d}@{SIMULATED_EMAIL_DOMAIN}'
            if Users.objects.filter(email=email).exists():
                # Sin --clear respetamos lo ya existente (idempotencia básica).
                continue

            user = self._make_user(rng, email, i, pwd)
            dog = self._make_dog(rng, user)
            plan_exercises, current_level = self._make_plan(
                rng, dog, levels, num_levels, by_level, reinforcements)

            if plan_exercises:
                skill = self._make_sessions(rng, dog, plan_exercises, now, window)
            else:
                skill = 0.6

            self._finish_user(rng, user, dog, skill, achievements, now, window)
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n{created} usuario(s) simulado(s) generado(s) '
            f'(semilla {opts["seed"]}, ventana {window} días).'))
        total_sim = sum(1 for _u, e in Users.objects.values_list('id', 'email')
                        if is_simulated_email(e))
        self.stdout.write(f'Total de usuarios simulados en la BD: {total_sim}.')

    def _make_user(self, rng, email, i, pwd):
        name = f'{rng.choice(FIRST_NAMES)} (sim {i})'
        user = Users.objects.create(
            id=str(uuid.uuid4()), name=name, email=email, password=pwd,
            experience_level=rng.choice(EXPERIENCE), total_xp=0,
        )
        UserStreaks.objects.create(
            id=str(uuid.uuid4()), user=user, current_streak=0, longest_streak=0)
        return user

    def _make_dog(self, rng, user):
        return Dogs.objects.create(
            id=str(uuid.uuid4()), user=user, name=rng.choice(DOG_NAMES),
            breed=rng.choice(BREEDS), age_months=rng.randint(4, 120),
            weight=round(rng.uniform(3, 40), 1), energy_level=rng.choice(ENERGY),
            training_level=1,
        )

    def _make_plan(self, rng, dog, levels, num_levels, by_level, reinforcements):
        """Crea el plan y sus ejercicios; devuelve (plan_exercises, current_idx)."""
        current_idx = rng.randint(0, num_levels - 1)  # 0-based
        current_level = levels[current_idx]
        dog.training_level = current_idx + 1
        dog.save(update_fields=['training_level'])

        plan = TrainingPlans.objects.create(
            id=str(uuid.uuid4()), dog=dog, current_level=current_level, active=True)

        plan_exercises = []
        order = 1
        for idx, level in enumerate(levels):
            if idx > current_idx:
                break
            is_past = idx < current_idx
            for ex in by_level.get(level.id, []):
                # Niveles pasados: dominados e inactivos. Nivel actual: mezcla.
                dominated = True if is_past else rng.random() < 0.4
                active = not is_past
                tpe = TrainingPlanExercises.objects.create(
                    id=str(uuid.uuid4()), training_plan=plan, exercise=ex,
                    reinforcement_type=rng.choice(reinforcements),
                    order_number=order, dominated=dominated, active=active)
                order += 1
                if active:
                    plan_exercises.append(tpe)
        return plan_exercises, current_idx

    def _make_sessions(self, rng, dog, plan_exercises, now, window):
        """Genera el historial de sesiones. Devuelve la 'habilidad' del perro."""
        skill = rng.uniform(0.4, 0.95)  # probabilidad base de éxito
        n_sessions = rng.randint(8, 40)

        for _ in range(n_sessions):
            tpe = rng.choice(plan_exercises)
            success = rng.random() < skill
            criteria_total = rng.randint(3, 5)
            if success:
                criteria_met = rng.randint(criteria_total - 1, criteria_total)
            else:
                criteria_met = rng.randint(0, max(0, criteria_total - 2))

            session = TrainingSessions.objects.create(
                id=str(uuid.uuid4()), dog=dog, exercise=tpe.exercise,
                reinforcement_type=tpe.reinforcement_type, success=success,
                response_time=rng.randint(2, 15),
                duration_seconds=rng.randint(30, 180),
                repetitions=rng.randint(3, 12),
                criteria_met=criteria_met, criteria_total=criteria_total,
            )
            # session_date es auto_now_add: se reescribe con .update() para
            # repartir el historial en la ventana (update no dispara auto_now_add).
            dt = now - timedelta(
                days=rng.randint(0, window - 1),
                hours=rng.randint(0, 23), minutes=rng.randint(0, 59))
            TrainingSessions.objects.filter(id=session.id).update(session_date=dt)
        return skill

    def _finish_user(self, rng, user, dog, skill, achievements, now, window):
        """Racha, XP, logros y encuesta SUS, coherentes con el desempeño."""
        sessions_count = TrainingSessions.objects.filter(dog=dog).count()
        successes = TrainingSessions.objects.filter(dog=dog, success=True).count()
        success_rate = (successes / sessions_count) if sessions_count else skill

        # Racha y XP plausibles.
        current_streak = rng.randint(0, 14)
        longest_streak = max(current_streak, rng.randint(current_streak, 30))
        UserStreaks.objects.filter(user=user).update(
            current_streak=current_streak, longest_streak=longest_streak)

        total_xp = sessions_count * 10 + successes * 10 + longest_streak * 2

        # Logros por hitos (solo los que existan en la BD).
        milestones = [
            ('Primera sesión', sessions_count >= 1),
            ('Racha de 3 días', longest_streak >= 3),
            ('Semana constante', longest_streak >= 7),
            ('10 sesiones completadas', sessions_count >= 10),
            ('50 sesiones completadas', sessions_count >= 50),
            ('Entrenador dedicado', longest_streak >= 30),
        ]
        for name, reached in milestones:
            ach = achievements.get(name)
            if reached and ach:
                UserAchievements.objects.create(
                    id=str(uuid.uuid4()), user=user, achievement=ach)
                total_xp += ach.xp_reward or 0

        Users.objects.filter(id=user.id).update(total_xp=total_xp)

        self._make_survey(rng, user, success_rate, now, window)

    def _make_survey(self, rng, user, success_rate, now, window):
        """Respuesta SUS correlacionada con la tasa de éxito (con ruido)."""
        # Satisfacción base 0..1 sesgada por el desempeño del perro.
        sat = min(1.0, max(0.0, 0.35 + success_rate * 0.55 + rng.uniform(-0.1, 0.1)))
        answers = []
        for i in range(1, 11):
            positive = (i % 2 == 1)
            noise = rng.randint(-1, 1)
            if positive:
                value = round(1 + sat * 4) + noise
            else:
                value = round(5 - sat * 4) + noise
            answers.append(min(5, max(1, value)))

        survey = SurveyResponses(
            id=str(uuid.uuid4()), user=user, is_simulated=True,
            **{f'q{i}': answers[i - 1] for i in range(1, 11)},
        )
        survey.sus_score = compute_sus_score(answers)  # save() lo recalcula igual
        survey.save()
        dt = now - timedelta(days=rng.randint(0, window - 1))
        SurveyResponses.objects.filter(id=survey.id).update(created_at=dt)
