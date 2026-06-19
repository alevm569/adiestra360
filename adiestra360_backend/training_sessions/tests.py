from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
import uuid

from testkit import (
    create_catalog, create_achievements, make_user, auth_client,
    create_dog, create_plan, create_session,
)
from training_sessions.models import TrainingSessions
from users.models import UserStreaks


class CreateSessionTests(TestCase):
    """POST /api/sessions/<dog_id>/create/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.achievements = create_achievements()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.exercise = self.catalog['exercises']['sientate']
        self.reinforcement = self.catalog['reinforcements']['comida']

    def _payload(self, **overrides):
        data = {
            'exercise': self.exercise.id,
            'reinforcement_type': self.reinforcement.id,
            'success': True,
            'response_time': 5,
            'duration_seconds': 60,
            'repetitions': 8,
        }
        data.update(overrides)
        return data

    def test_create_session_success(self):
        response = self.client.post(
            f'/api/sessions/{self.dog.id}/create/', self._payload(), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('session', response.data)
        self.assertIn('xp_earned', response.data)
        self.assertIn('streak', response.data)
        self.assertIn('exercise_stats', response.data)
        self.assertTrue(
            TrainingSessions.objects.filter(dog=self.dog).exists()
        )

    def test_create_session_first_session_starts_streak_at_one(self):
        # Regresión del bug: la primera sesión (racha en 0, creada hoy en el
        # registro) debe iniciar la racha en 1, no quedarse en 0.
        response = self.client.post(
            f'/api/sessions/{self.dog.id}/create/', self._payload(), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['streak']['current'], 1)
        streak = UserStreaks.objects.get(user=self.user)
        self.assertEqual(streak.current_streak, 1)

    def test_create_session_accumulates_total_xp(self):
        # Regresión #5: el XP de la sesión + el de los logros se persiste
        # en user.total_xp (antes el xp_earned se perdía).
        response = self.client.post(
            f'/api/sessions/{self.dog.id}/create/', self._payload(), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        achievement_xp = sum(a['xp_reward'] for a in response.data['new_achievements'])
        self.user.refresh_from_db()
        self.assertGreater(self.user.total_xp, 0)
        self.assertEqual(self.user.total_xp, response.data['xp_earned'] + achievement_xp)
        self.assertEqual(response.data['total_xp'], self.user.total_xp)

    def test_create_session_unlocks_first_session_achievement(self):
        response = self.client.post(
            f'/api/sessions/{self.dog.id}/create/', self._payload(), format='json'
        )
        names = [a['name'] for a in response.data['new_achievements']]
        self.assertIn('Primera sesión', names)

    def test_create_session_invalid_data_fails(self):
        # Falta el ejercicio (FK obligatoria)
        response = self.client.post(
            f'/api/sessions/{self.dog.id}/create/',
            {'reinforcement_type': self.reinforcement.id, 'success': True},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_session_dog_not_found(self):
        response = self.client.post(
            f'/api/sessions/{uuid.uuid4()}/create/', self._payload(), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_session_unauthenticated(self):
        self.client.credentials()
        response = self.client.post(
            f'/api/sessions/{self.dog.id}/create/', self._payload(), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class StreakBehaviorTests(TestCase):
    """Comportamiento de la racha al registrar sesiones (update_streak)."""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.exercise = self.catalog['exercises']['sientate']
        self.reinforcement = self.catalog['reinforcements']['comida']

    def _post_session(self):
        return self.client.post(
            f'/api/sessions/{self.dog.id}/create/',
            {
                'exercise': self.exercise.id,
                'reinforcement_type': self.reinforcement.id,
                'success': True,
                'response_time': 5,
            },
            format='json',
        )

    def _set_streak(self, current, days_ago):
        # update() no dispara auto_now, así que respeta la fecha indicada.
        moment = timezone.now() - timedelta(days=days_ago)
        UserStreaks.objects.filter(user=self.user).update(
            current_streak=current, longest_streak=current, updated_at=moment
        )

    def test_streak_increments_when_trained_yesterday(self):
        self._set_streak(current=3, days_ago=1)
        response = self._post_session()
        self.assertEqual(response.data['streak']['current'], 4)
        self.assertEqual(response.data['streak']['longest'], 4)

    def test_streak_resets_after_gap(self):
        self._set_streak(current=5, days_ago=4)
        response = self._post_session()
        self.assertEqual(response.data['streak']['current'], 1)
        # La racha más larga se conserva
        self.assertEqual(response.data['streak']['longest'], 5)

    def test_streak_not_double_counted_same_day(self):
        self._post_session()  # arranca en 1
        response = self._post_session()  # misma fecha, no debe sumar
        self.assertEqual(response.data['streak']['current'], 1)


class ListSessionsTests(TestCase):
    """GET /api/sessions/<dog_id>/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.ex1 = self.catalog['exercises']['sientate']
        self.ex2 = self.catalog['exercises']['echate']
        self.ref = self.catalog['reinforcements']['comida']
        create_session(self.dog, self.ex1, self.ref, success=True)
        create_session(self.dog, self.ex1, self.ref, success=False)
        create_session(self.dog, self.ex2, self.ref, success=True)

    def test_list_sessions(self):
        response = self.client.get(f'/api/sessions/{self.dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_sessions_filtered_by_exercise(self):
        response = self.client.get(f'/api/sessions/{self.dog.id}/?exercise_id={self.ex1.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_sessions_empty(self):
        empty_dog = create_dog(self.user, name='Sin sesiones')
        response = self.client.get(f'/api/sessions/{empty_dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_sessions_dog_not_found(self):
        response = self.client.get(f'/api/sessions/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_sessions_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(f'/api/sessions/{self.dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SessionStatsTests(TestCase):
    """GET /api/sessions/<dog_id>/stats/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.ex1 = self.catalog['exercises']['sientate']
        self.ref_comida = self.catalog['reinforcements']['comida']
        self.ref_pelota = self.catalog['reinforcements']['pelota']

    def test_stats_zero_sessions(self):
        response = self.client.get(f'/api/sessions/{self.dog.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_sessions'], 0)
        self.assertEqual(response.data['success_rate'], 0)
        self.assertEqual(response.data['by_exercise'], [])

    def test_stats_with_sessions(self):
        # 3 con comida (2 éxito), 1 con pelota (1 éxito)
        create_session(self.dog, self.ex1, self.ref_comida, success=True, response_time=4)
        create_session(self.dog, self.ex1, self.ref_comida, success=True, response_time=6)
        create_session(self.dog, self.ex1, self.ref_comida, success=False, response_time=10)
        create_session(self.dog, self.ex1, self.ref_pelota, success=True, response_time=3)

        response = self.client.get(f'/api/sessions/{self.dog.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_sessions'], 4)
        self.assertEqual(response.data['success_rate'], 75.0)
        self.assertEqual(len(response.data['by_exercise']), 1)
        self.assertEqual(len(response.data['by_reinforcement']), 2)
        # pelota (100%) debe quedar de primero al ordenar por éxito
        self.assertEqual(response.data['best_reinforcement'], 'Pelota')

    def test_stats_dog_not_found(self):
        response = self.client.get(f'/api/sessions/{uuid.uuid4()}/stats/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_stats_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(f'/api/sessions/{self.dog.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
