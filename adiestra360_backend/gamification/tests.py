from django.test import TestCase
from rest_framework import status
import uuid

from testkit import (
    create_catalog, create_achievements, make_user, auth_client,
    create_dog, create_plan, create_session,
)
from gamification.models import UserAchievements


def grant(user, achievement):
    return UserAchievements.objects.create(
        id=str(uuid.uuid4()), user=user, achievement=achievement
    )


class ListAchievementsTests(TestCase):
    """GET /api/gamification/achievements/"""

    def setUp(self):
        self.achievements = create_achievements()
        self.user = make_user()
        self.client = auth_client(self.user)

    def test_list_achievements(self):
        response = self.client.get('/api/gamification/achievements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.achievements))

    def test_list_achievements_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/api/gamification/achievements/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserAchievementsTests(TestCase):
    """GET /api/gamification/my-achievements/"""

    def setUp(self):
        self.achievements = create_achievements()
        self.user = make_user()
        self.client = auth_client(self.user)
        grant(self.user, self.achievements['Primera sesión'])

    def test_user_achievements_earned_and_pending(self):
        response = self.client.get('/api/gamification/my-achievements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_earned'], 1)
        self.assertEqual(response.data['total_available'], len(self.achievements))
        self.assertEqual(len(response.data['pending']), len(self.achievements) - 1)
        self.assertEqual(response.data['earned'][0]['achievement']['name'], 'Primera sesión')

    def test_user_achievements_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/api/gamification/my-achievements/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserStatsTests(TestCase):
    """GET /api/gamification/stats/"""

    def setUp(self):
        self.achievements = create_achievements()
        self.user = make_user()
        self.client = auth_client(self.user)

    def test_user_stats_beginner_no_xp(self):
        response = self.client.get('/api/gamification/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_xp'], 0)
        self.assertEqual(response.data['user_level'], 'Principiante')
        self.assertEqual(response.data['streak']['current'], 0)

    def test_user_stats_levels_up_with_xp(self):
        # 2 logros desbloqueados; el XP total acumulado vive en user.total_xp.
        grant(self.user, self.achievements['Semana constante'])
        grant(self.user, self.achievements['50 sesiones completadas'])
        self.user.total_xp = 150  # 50 + 100
        self.user.save()
        response = self.client.get('/api/gamification/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_xp'], 150)
        self.assertEqual(response.data['user_level'], 'Intermedio')
        self.assertEqual(response.data['achievements_earned'], 2)

    def test_user_stats_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/api/gamification/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DashboardTests(TestCase):
    """GET /api/gamification/dashboard/<dog_id>/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.achievements = create_achievements()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.ex = self.catalog['exercises']['sientate']
        self.ref = self.catalog['reinforcements']['comida']
        self.plan, _ = create_plan(
            self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.ref)]
        )
        create_session(self.dog, self.ex, self.ref, success=True)
        create_session(self.dog, self.ex, self.ref, success=False)

    def test_dashboard_success(self):
        response = self.client.get(f'/api/gamification/dashboard/{self.dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['dog']['id'], str(self.dog.id))
        self.assertIsNotNone(response.data['plan'])
        self.assertEqual(response.data['stats']['total_sessions'], 2)
        self.assertEqual(response.data['stats']['success_rate'], 50.0)
        self.assertEqual(len(response.data['exercise_progress']), 1)
        self.assertIn('gamification', response.data)

    def test_dashboard_dog_not_found(self):
        response = self.client.get(f'/api/gamification/dashboard/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_dashboard_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(f'/api/gamification/dashboard/{self.dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
