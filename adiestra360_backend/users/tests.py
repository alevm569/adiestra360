from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Users, UserStreaks
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
            'experience_level': 'principiante'
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
            'password': 'test1234'
        }
        self.client.post(self.url, data, format='json')
        user = Users.objects.get(email='valery@test.com')
        self.assertTrue(UserStreaks.objects.filter(user=user).exists())

    def test_register_duplicate_email_fails(self):
        data = {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234'
        }
        self.client.post(self.url, data, format='json')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields_fails(self):
        response = self.client.post(self.url, {'email': 'a@a.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_too_short_fails(self):
        data = {'name': 'Valery', 'email': 'valery@test.com', 'password': '123'}
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
            'password': 'test1234'
        }, format='json')

    def test_login_success(self):
        response = self.client.post(self.login_url, {
            'email': 'valery@test.com',
            'password': 'test1234'
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
            'password': 'test1234'
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
            'password': 'test1234'
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


class QuizQuestionsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_quiz_returns_questions(self):
        response = self.client.get('/api/auth/quiz/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 11)
        self.assertIn('category', response.data[0])