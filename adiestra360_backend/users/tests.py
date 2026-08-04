from datetime import timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from .models import Users, UserStreaks, PasswordResetCodes
import uuid


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/auth/register/'

    def test_register_success(self):
        data = {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234',
            'experience_level': 'principiante',
            'research_consent': True,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertEqual(response.data['user']['email'], 'valery@test.com')

    def test_register_creates_streak(self):
        data = {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234',
            'research_consent': True,
        }
        self.client.post(self.url, data, format='json')
        user = Users.objects.get(email='valery@test.com')
        self.assertTrue(UserStreaks.objects.filter(user=user).exists())

    def test_register_duplicate_email_fails(self):
        data = {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234',
            'research_consent': True,
        }
        self.client.post(self.url, data, format='json')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields_fails(self):
        response = self.client.post(self.url, {'email': 'a@a.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_too_short_fails(self):
        data = {'name': 'Valery', 'email': 'valery@test.com',
                'password': '123', 'research_consent': True}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/auth/register/'
        self.login_url = '/api/auth/login/'
        self.client.post(self.register_url, {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234',
            'research_consent': True,
        }, format='json')

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'email': 'valery@test.com',
            'password': 'test1234',
            'research_consent': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('streak', response.data)

    def test_login_wrong_password_fails(self):
        response = self.client.post(self.login_url, {
            'email': 'valery@test.com',
            'password': 'wrongpass'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_email_fails(self):
        response = self.client.post(self.login_url, {
            'email': 'noexiste@test.com',
            'password': 'test1234',
            'research_consent': True,
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields_fails(self):
        response = self.client.post(self.login_url, {'email': 'valery@test.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        register_response = self.client.post('/api/auth/register/', {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234',
            'research_consent': True,
        }, format='json')
        self.token = register_response.data['tokens']['access']

    def test_profile_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], 'valery@test.com')

    def test_profile_unauthenticated_fails(self):
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    """Flujo de recuperación: pedir código por correo y cambiar la contraseña."""

    def setUp(self):
        self.client = APIClient()
        self.request_url = '/api/auth/password-reset/'
        self.confirm_url = '/api/auth/password-reset/confirm/'
        self.login_url = '/api/auth/login/'
        self.client.post('/api/auth/register/', {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234',
            'research_consent': True,
        }, format='json')
        mail.outbox = []

    def _request_code(self, email='valery@test.com'):
        """Pide un código y lo extrae del correo enviado."""
        response = self.client.post(self.request_url, {'email': email},
                                    format='json')
        code = None
        if mail.outbox:
            code = next(w for w in mail.outbox[-1].body.split()
                        if w.isdigit() and len(w) == 6)
        return response, code

    def test_request_sends_email_with_code(self):
        response, code = self._request_code()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['valery@test.com'])
        self.assertIsNotNone(code)

    def test_request_unknown_email_does_not_reveal_and_sends_nothing(self):
        response = self.client.post(self.request_url,
                                    {'email': 'noexiste@test.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)
        # Mismo cuerpo que con un correo real: no delata quién está registrado.
        known = self.client.post(self.request_url, {'email': 'valery@test.com'},
                                 format='json')
        self.assertEqual(response.data['message'], known.data['message'])

    def test_request_missing_email_fails(self):
        response = self.client.post(self.request_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_code_is_not_stored_in_plain_text(self):
        _, code = self._request_code()
        entry = PasswordResetCodes.objects.get()
        self.assertNotIn(code, entry.code_hash)

    def test_confirm_changes_password_and_returns_tokens(self):
        _, code = self._request_code()
        response = self.client.post(self.confirm_url, {
            'email': 'valery@test.com',
            'code': code,
            'new_password': 'nueva1234',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)

        # La nueva sirve y la vieja ya no.
        nueva = self.client.post(self.login_url, {
            'email': 'valery@test.com', 'password': 'nueva1234'}, format='json')
        self.assertEqual(nueva.status_code, status.HTTP_200_OK)
        vieja = self.client.post(self.login_url, {
            'email': 'valery@test.com', 'password': 'test1234'}, format='json')
        self.assertEqual(vieja.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_code_can_be_used_only_once(self):
        _, code = self._request_code()
        payload = {'email': 'valery@test.com', 'code': code,
                   'new_password': 'nueva1234'}
        self.client.post(self.confirm_url, payload, format='json')
        segunda = self.client.post(self.confirm_url, payload, format='json')
        self.assertEqual(segunda.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_code_fails_and_keeps_old_password(self):
        self._request_code()
        response = self.client.post(self.confirm_url, {
            'email': 'valery@test.com',
            'code': '000000',
            'new_password': 'nueva1234',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        user = Users.objects.get(email='valery@test.com')
        self.assertTrue(user.check_password('test1234'))

    def test_expired_code_fails(self):
        _, code = self._request_code()
        PasswordResetCodes.objects.update(
            expires_at=timezone.now() - timedelta(minutes=1))
        response = self.client.post(self.confirm_url, {
            'email': 'valery@test.com',
            'code': code,
            'new_password': 'nueva1234',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(PASSWORD_RESET_MAX_ATTEMPTS=2)
    def test_code_dies_after_too_many_attempts(self):
        _, code = self._request_code()
        for _ in range(2):
            self.client.post(self.confirm_url, {
                'email': 'valery@test.com', 'code': '000000',
                'new_password': 'nueva1234'}, format='json')
        # Aunque ahora acierte, el código ya está quemado.
        response = self.client.post(self.confirm_url, {
            'email': 'valery@test.com', 'code': code,
            'new_password': 'nueva1234'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(PASSWORD_RESET_RESEND_SECONDS=0)
    def test_new_code_invalidates_the_previous_one(self):
        _, primero = self._request_code()
        _, segundo = self._request_code()
        self.assertNotEqual(primero, segundo)
        viejo = self.client.post(self.confirm_url, {
            'email': 'valery@test.com', 'code': primero,
            'new_password': 'nueva1234'}, format='json')
        self.assertEqual(viejo.status_code, status.HTTP_400_BAD_REQUEST)
        nuevo = self.client.post(self.confirm_url, {
            'email': 'valery@test.com', 'code': segundo,
            'new_password': 'nueva1234'}, format='json')
        self.assertEqual(nuevo.status_code, status.HTTP_200_OK)

    def test_resend_too_soon_does_not_send_another_email(self):
        self._request_code()
        self.client.post(self.request_url, {'email': 'valery@test.com'},
                         format='json')
        self.assertEqual(len(mail.outbox), 1)

    def test_short_password_is_rejected(self):
        _, code = self._request_code()
        response = self.client.post(self.confirm_url, {
            'email': 'valery@test.com', 'code': code, 'new_password': '123',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_missing_fields_fails(self):
        response = self.client.post(self.confirm_url,
                                    {'email': 'valery@test.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class QuizQuestionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_quiz_returns_questions(self):
        response = self.client.get('/api/auth/quiz/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 11)
        self.assertIn('category', response.data[0])