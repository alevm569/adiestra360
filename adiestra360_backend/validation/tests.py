"""
Tests de la fase de validación: scoring SUS, upsert de la encuesta y el
gateado por email del panel de métricas.

    python manage.py test validation
"""
import os
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from users import announcements
from testkit import make_user, auth_client, create_dog
from .constants import compute_sus_score, is_simulated_email, SIMULATED_EMAIL_DOMAIN
from .metrics import build_metrics
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


class MultiDogCountTests(APITestCase):
    """
    El panel muestra a cuánta gente le aplican las notas de "más de un perro",
    así que el conteo debe ser de dueños, no de perros.
    """

    def test_counts_owners_with_more_than_one_dog(self):
        uno = make_user(email='uno@test.com', name='Uno')
        dos = make_user(email='dos@test.com', name='Dos')
        tres = make_user(email='tres@test.com', name='Tres')
        create_dog(uno, name='Luna')
        create_dog(dos, name='Rocky')
        create_dog(dos, name='Toby')
        create_dog(tres, name='Kira')
        create_dog(tres, name='Nala')
        create_dog(tres, name='Zeus')

        usage = build_metrics()['combined']['usage']
        self.assertEqual(usage['users'], 3)
        self.assertEqual(usage['dogs'], 6)
        self.assertEqual(usage['multi_dog_users'], 2)
        self.assertEqual(usage['max_dogs_per_user'], 3)

    def test_zero_when_nobody_has_dogs(self):
        make_user(email='solo@test.com', name='Solo')
        usage = build_metrics()['combined']['usage']
        self.assertEqual(usage['multi_dog_users'], 0)
        self.assertEqual(usage['max_dogs_per_user'], 0)


class SimulatedEmailTests(APITestCase):
    def test_domain_detection(self):
        self.assertTrue(is_simulated_email(f'sim-001@{SIMULATED_EMAIL_DOMAIN}'))
        self.assertFalse(is_simulated_email('real@gmail.com'))


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class AnnouncementTests(APITestCase):
    """
    El aviso masivo va a los correos reales de los participantes, así que lo
    que se comprueba es quién puede dispararlo y a quién llega.
    """

    def setUp(self):
        self.admin = make_user(email='boss@test.com', name='Boss')
        self.plain = make_user(email='user@test.com', name='User')
        self.simulado = make_user(email=f'sim-001@{SIMULATED_EMAIL_DOMAIN}',
                                  name='Simulado')
        os.environ['VALIDATION_ADMIN_EMAILS'] = 'boss@test.com'
        self.addCleanup(os.environ.pop, 'VALIDATION_ADMIN_EMAILS', None)
        mail.outbox = []

    def test_non_admin_forbidden(self):
        res = auth_client(self.plain).post('/api/validation/announcement/')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(len(mail.outbox), 0)

    def test_dry_run_lists_recipients_without_sending(self):
        res = auth_client(self.admin).post(
            '/api/validation/announcement/', {'dry_run': True}, format='json')
        self.assertEqual(res.status_code, 200)
        emails = [r['email'] for r in res.data['recipients']]
        self.assertIn('user@test.com', emails)
        self.assertEqual(len(mail.outbox), 0)

    def test_sends_one_email_per_real_user(self):
        res = auth_client(self.admin).post('/api/validation/announcement/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['sent'], 2)
        self.assertEqual(res.data['failed'], [])
        # Un mensaje por persona: nadie ve la dirección de los demás.
        self.assertEqual(len(mail.outbox), 2)
        for message in mail.outbox:
            self.assertEqual(len(message.to), 1)
            self.assertEqual(message.cc, [])
            self.assertEqual(message.bcc, [])

    def test_simulated_users_excluded_by_default(self):
        auth_client(self.admin).post('/api/validation/announcement/')
        destinatarios = {m.to[0] for m in mail.outbox}
        self.assertNotIn(self.simulado.email, destinatarios)

    def test_body_greets_each_user_by_name(self):
        auth_client(self.admin).post('/api/validation/announcement/')
        cuerpos = {m.to[0]: m.body for m in mail.outbox}
        self.assertIn('Hola User:', cuerpos['user@test.com'])
        self.assertIn(announcements.DEADLINE, cuerpos['user@test.com'])

    def test_one_failure_does_not_stop_the_rest(self):
        # Un rebote no puede dejar sin avisar a los demás participantes.
        original = announcements.send_to

        def flaky(user, subject=None, template=None):
            if user.email == 'boss@test.com':
                return 'SMTPException: rebotado'
            return original(user, subject, template)

        with patch.object(announcements, 'send_to', flaky):
            res = auth_client(self.admin).post('/api/validation/announcement/')

        self.assertEqual(res.data['sent'], 1)
        self.assertEqual(res.data['failed'],
                         [{'email': 'boss@test.com', 'error': 'SMTPException: rebotado'}])
