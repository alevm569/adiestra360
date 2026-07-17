from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Dogs
from training.models import (
    TrainingLevels, Exercises, ReinforcementTypes,
    TrainingPlans, TrainingPlanExercises
)
from training.constants import (
    NIVEL1, NIVEL1_SLUGS, SIENTATE, ECHATE, AQUI, QUEDATE, LUGAR, JUNTO,
)
import uuid


def create_base_catalog():
    """
    Crea el catálogo mínimo necesario para que el quiz y el
    generador de planes funcionen: niveles, ejercicios y refuerzos.
    """
    lvl1 = TrainingLevels.objects.create(id='lvl-001', name='Nivel 1', description='Obediencia básica')
    lvl2 = TrainingLevels.objects.create(id='lvl-002', name='Nivel 2', description='Obediencia intermedia')

    # Los 6 ejercicios de Nivel 1 salen de training.constants, en su orden.
    for i, (_slug, name) in enumerate(NIVEL1, start=1):
        Exercises.objects.create(
            id=f'ex-{i:03d}', level=lvl1, name=name,
            description='desc', difficulty=i, estimated_duration=10
        )

    reinforcements = [
        ('ref-001', 'Comida'),
        ('ref-002', 'Pelota'),
        ('ref-003', 'Caricias'),
        ('ref-004', 'Clicker'),
        ('ref-005', 'Juguete'),
    ]
    for ref_id, name in reinforcements:
        ReinforcementTypes.objects.create(id=ref_id, name=name)

    return lvl1, lvl2


class CreateDogProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        create_base_catalog()

        register_response = self.client.post('/api/auth/register/', {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234'
        }, format='json')
        self.token = register_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.quiz_answers = [
            {'exercise_related': AQUI, 'answer': 'Siempre'},
            {'exercise_related': SIENTATE, 'answer': 'Siempre'},
            {'exercise_related': ECHATE, 'answer': 'A veces'},
            {'exercise_related': QUEDATE, 'answer': 'Casi nunca'},
            {'exercise_related': JUNTO, 'answer': 'Nunca'},
            {'exercise_related': LUGAR, 'answer': 'Nunca'},
            {'reinforcement_related': 'pelota', 'answer': 'Mucho'},
            {'reinforcement_related': 'comida', 'answer': 'Algo'},
            {'reinforcement_related': 'caricias', 'answer': 'Poco'},
            {'experience_related': 'experience_level', 'answer': 'Solo lo básico'},
        ]

    def test_create_dog_profile_success(self):
        data = {
            'dog': {
                'name': 'Luna',
                'breed': 'Cocker',
                'age_months': 18,
                'weight': 25.5,
                'energy_level': 'alto'
            },
            'quiz_answers': self.quiz_answers
        }
        response = self.client.post('/api/dogs/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['training_level'], 1)
        self.assertEqual(response.data['initial_reinforcement'], 'pelota')
        self.assertIn(SIENTATE, response.data['dominated_exercises'])
        self.assertIn(AQUI, response.data['dominated_exercises'])

    def test_create_dog_generates_plan(self):
        data = {
            'dog': {'name': 'Luna', 'breed': 'Cocker', 'age_months': 18,
                     'weight': 25.5, 'energy_level': 'alto'},
            'quiz_answers': self.quiz_answers
        }
        response = self.client.post('/api/dogs/create/', data, format='json')
        plan_id = response.data['plan_id']
        self.assertTrue(TrainingPlans.objects.filter(id=plan_id).exists())
        plan = TrainingPlans.objects.get(id=plan_id)
        self.assertTrue(TrainingPlanExercises.objects.filter(training_plan=plan).exists())

    def test_create_dog_without_quiz_fails(self):
        data = {'dog': {'name': 'Luna', 'breed': 'Cocker'}}
        response = self.client.post('/api/dogs/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_dog_without_dog_data_fails(self):
        data = {'quiz_answers': self.quiz_answers}
        response = self.client.post('/api/dogs/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_dog_unauthenticated_fails(self):
        self.client.credentials()  # limpia el header de auth
        data = {
            'dog': {'name': 'Luna'},
            'quiz_answers': self.quiz_answers
        }
        response = self.client.post('/api/dogs/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dog_with_all_exercises_known_goes_to_level2(self):
        full_knowledge_answers = [
            {'exercise_related': ex, 'answer': 'Siempre'}
            for ex in NIVEL1_SLUGS
        ]
        data = {
            'dog': {'name': 'Rocky', 'breed': 'Labrador', 'energy_level': 'medio'},
            'quiz_answers': full_knowledge_answers
        }
        # Sin Nivel 2 con ejercicios en el catálogo de prueba, el sistema
        # debe seguir respondiendo 201 aunque no pueda generar ejercicios nuevos
        response = self.client.post('/api/dogs/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['training_level'], 2)


class ListAndDetailDogTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        create_base_catalog()

        register_response = self.client.post('/api/auth/register/', {
            'name': 'Valery',
            'email': 'valery@test.com',
            'password': 'test1234'
        }, format='json')
        self.token = register_response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        quiz_answers = [
            {'exercise_related': SIENTATE, 'answer': 'Siempre'},
            {'reinforcement_related': 'comida', 'answer': 'Mucho'},
        ]
        create_response = self.client.post('/api/dogs/create/', {
            'dog': {'name': 'Luna', 'breed': 'Cocker', 'energy_level': 'medio'},
            'quiz_answers': quiz_answers
        }, format='json')
        self.dog_id = create_response.data['dog']['id']

    def test_list_dogs(self):
        response = self.client.get('/api/dogs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Luna')

    def test_dog_detail(self):
        response = self.client.get(f'/api/dogs/{self.dog_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Luna')

    def test_dog_detail_not_found(self):
        fake_id = str(uuid.uuid4())
        response = self.client.get(f'/api/dogs/{fake_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_dog(self):
        response = self.client.put(f'/api/dogs/{self.dog_id}/update/', {
            'name': 'Luna Actualizada'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Luna Actualizada')

    def test_update_dog_partial_preserves_other_fields(self):
        response = self.client.put(f'/api/dogs/{self.dog_id}/update/', {
            'breed': 'Pastor Alemán'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['breed'], 'Pastor Alemán')
        self.assertEqual(response.data['name'], 'Luna')  # se conserva

    def test_update_dog_not_found(self):
        fake_id = str(uuid.uuid4())
        response = self.client.put(f'/api/dogs/{fake_id}/update/', {
            'name': 'X'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_dogs_unauthenticated(self):
        self.client.credentials()
        response = self.client.get('/api/dogs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dog_detail_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(f'/api/dogs/{self.dog_id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_dog_unauthenticated(self):
        self.client.credentials()
        response = self.client.put(f'/api/dogs/{self.dog_id}/update/', {
            'name': 'X'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CrossUserAccessTests(TestCase):
    """Un usuario no puede ver ni modificar perros de otro usuario."""

    def setUp(self):
        self.client = APIClient()
        create_base_catalog()

        # Usuario dueño del perro
        owner_resp = self.client.post('/api/auth/register/', {
            'name': 'Dueño', 'email': 'owner@test.com', 'password': 'test1234'
        }, format='json')
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {owner_resp.data['tokens']['access']}"
        )
        create_resp = self.client.post('/api/dogs/create/', {
            'dog': {'name': 'Luna', 'breed': 'Cocker', 'energy_level': 'medio'},
            'quiz_answers': [
                {'exercise_related': SIENTATE, 'answer': 'Siempre'},
                {'reinforcement_related': 'comida', 'answer': 'Mucho'},
            ]
        }, format='json')
        self.dog_id = create_resp.data['dog']['id']

        # Segundo usuario (intruso); el cliente queda autenticado como él
        intruder_resp = self.client.post('/api/auth/register/', {
            'name': 'Intruso', 'email': 'intruder@test.com', 'password': 'test1234'
        }, format='json')
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {intruder_resp.data['tokens']['access']}"
        )

    def test_intruder_cannot_see_dog(self):
        response = self.client.get(f'/api/dogs/{self.dog_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_intruder_cannot_update_dog(self):
        response = self.client.put(f'/api/dogs/{self.dog_id}/update/', {
            'name': 'Hackeado'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_intruder_dog_not_in_list(self):
        response = self.client.get('/api/dogs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)


class ExperienceLevelTests(TestCase):
    """
    Regresión #6: el nivel de experiencia se calcula promediando AMBAS
    preguntas del quiz (10 y 11), no solo la primera.
    """

    def test_experience_is_averaged_between_both_questions(self):
        from dogs.views import calculate_experience_level
        answers = [
            {'experience_related': 'experience_level', 'answer': 'Sí, tengo experiencia'},  # avanzado
            {'experience_related': 'experience_level', 'answer': 'No lo conozco'},           # principiante
        ]
        # Promedio (avanzado + principiante) → intermedio
        self.assertEqual(calculate_experience_level(answers), 'intermedio')

    def test_experience_both_advanced(self):
        from dogs.views import calculate_experience_level
        answers = [
            {'experience_related': 'experience_level', 'answer': 'Sí, tengo experiencia'},
            {'experience_related': 'experience_level', 'answer': 'Sí, lo aplico'},
        ]
        self.assertEqual(calculate_experience_level(answers), 'avanzado')

    def test_experience_no_answers_defaults_beginner(self):
        from dogs.views import calculate_experience_level
        self.assertEqual(calculate_experience_level([]), 'principiante')