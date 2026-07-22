"""
Tests de la fase de validación: scoring SUS, upsert de la encuesta y el
gateado por email del panel de métricas.

    python manage.py test validation
"""
from django.test import override_settings
from rest_framework.test import APITestCase

from testkit import make_user, auth_client
from .constants import compute_sus_score, is_simulated_email, SIMULATED_EMAIL_DOMAIN
from .models import SurveyResponses


class SusScoringTests(APITestCase):
    def test_all_min_answers_score_zero(self):
        # Positivos=1 (peor), negativos=5 (peor) -> 0.
        answers = [1, 5, 1, 5, 1, 5, 1, 5, 1, 5]
        self.assertEqual(compute_sus_score(answers), 0.0)

    def test_all_best_answers_score_100(self):
        # Positivos=5 (mejor), negativos=1 (mejor) -> 100.
        answers = [5, 1, 5, 1, 5, 1, 5, 1, 5, 1]
        self.assertEqual(compute_sus_score(answers), 100.0)

    def test_all_neutral_scores_50(self):
        self.assertEqual(compute_sus_score([3] * 10), 50.0)

    def test_wrong_length_raises(self):
        with self.assertRaises(ValueError):
            compute_sus_score([3, 3, 3])


class SurveyEndpointTests(APITestCase):
    def setUp(self):
        self.user = make_user(email='owner@test.com')
        self.client = auth_client(self.user)

    def _payload(self, answers):
        return {f'q{i}': v for i, v in enumerate(answers, start=1)}

    def test_get_returns_questions_and_null_response(self):
        res = self.client.get('/api/validation/survey/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['questions']), 10)
        self.assertIsNone(res.data['response'])

    def test_post_creates_and_scores(self):
        res = self.client.post(
            '/api/validation/survey/',
            self._payload([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]),
            format='json',
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(float(res.data['sus_score']), 100.0)
        self.assertFalse(res.data['is_simulated'])

    def test_post_is_upsert_one_per_user(self):
        self.client.post('/api/validation/survey/',
                         self._payload([3] * 10), format='json')
        res = self.client.post('/api/validation/survey/',
                               self._payload([5, 1, 5, 1, 5, 1, 5, 1, 5, 1]),
                               format='json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(SurveyResponses.objects.filter(user=self.user).count(), 1)
        self.assertEqual(float(res.data['sus_score']), 100.0)

    def test_out_of_range_rejected(self):
        res = self.client.post('/api/validation/survey/',
                               self._payload([9, 1, 5, 1, 5, 1, 5, 1, 5, 1]),
                               format='json')
        self.assertEqual(res.status_code, 400)


@override_settings()
class MetricsPermissionTests(APITestCase):
    def setUp(self):
        self.admin = make_user(email='boss@test.com', name='Boss')
        self.plain = make_user(email='user@test.com', name='User')

    def test_non_admin_forbidden(self):
        client = auth_client(self.plain)
        import os
        os.environ['VALIDATION_ADMIN_EMAILS'] = 'boss@test.com'
        try:
            self.assertEqual(client.get('/api/validation/metrics/').status_code, 403)
        finally:
            os.environ.pop('VALIDATION_ADMIN_EMAILS', None)

    def test_admin_allowed(self):
        import os
        os.environ['VALIDATION_ADMIN_EMAILS'] = 'boss@test.com'
        try:
            client = auth_client(self.admin)
            res = client.get('/api/validation/metrics/')
            self.assertEqual(res.status_code, 200)
            self.assertIn('combined', res.data)
        finally:
            os.environ.pop('VALIDATION_ADMIN_EMAILS', None)


class SimulatedEmailTests(APITestCase):
    def test_domain_detection(self):
        self.assertTrue(is_simulated_email(f'sim-001@{SIMULATED_EMAIL_DOMAIN}'))
        self.assertFalse(is_simulated_email('real@gmail.com'))
