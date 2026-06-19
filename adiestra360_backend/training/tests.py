from django.test import TestCase
from rest_framework import status
import uuid

from testkit import (
    create_catalog, make_user, auth_client, create_dog,
    create_plan, create_session,
)
from training.models import (
    TrainingLevels, Exercises, ReinforcementTypes,
    TrainingPlans, TrainingPlanExercises,
)


class TrainingCatalogTests(TestCase):
    """GET /levels/, /exercises/, /reinforcements/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)

    def test_list_levels(self):
        response = self.client.get('/api/training/levels/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_exercises_returns_all(self):
        response = self.client.get('/api/training/exercises/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)  # 3 nivel 1 + 3 nivel 2

    def test_list_exercises_filtered_by_level(self):
        lvl1_id = self.catalog['levels']['lvl1'].id
        response = self.client.get(f'/api/training/exercises/?level_id={lvl1_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_list_reinforcements(self):
        response = self.client.get('/api/training/reinforcements/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_catalog_requires_authentication(self):
        self.client.credentials()  # limpia el header
        response = self.client.get('/api/training/exercises/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ActivePlanTests(TestCase):
    """GET /plan/<dog_id>/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.plan, _ = create_plan(
            self.dog,
            self.catalog['levels']['lvl1'],
            [(self.catalog['exercises']['sientate'], self.catalog['reinforcements']['comida'])],
        )

    def test_get_active_plan_success(self):
        response = self.client.get(f'/api/training/plan/{self.dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.plan.id)
        self.assertEqual(len(response.data['exercises']), 1)

    def test_get_active_plan_dog_not_found(self):
        response = self.client.get(f'/api/training/plan/{uuid.uuid4()}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_active_plan_no_active_plan(self):
        self.plan.active = False
        self.plan.save()
        response = self.client.get(f'/api/training/plan/{self.dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_active_plan_of_another_user_dog(self):
        other_user = make_user(email='other@test.com')
        other_dog = create_dog(other_user, name='Toby')
        create_plan(
            other_dog, self.catalog['levels']['lvl1'],
            [(self.catalog['exercises']['sientate'], self.catalog['reinforcements']['comida'])],
        )
        # El cliente autenticado como self.user no puede ver el perro ajeno
        response = self.client.get(f'/api/training/plan/{other_dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_active_plan_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(f'/api/training/plan/{self.dog.id}/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EvaluateProgressTests(TestCase):
    """POST /plan/<dog_id>/evaluate/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.ex_sientate = self.catalog['exercises']['sientate']
        self.ex_echate = self.catalog['exercises']['echate']
        self.comida = self.catalog['reinforcements']['comida']

    def test_evaluate_requires_exercise_id(self):
        create_plan(self.dog, self.catalog['levels']['lvl1'],
                    [(self.ex_sientate, self.comida)])
        response = self.client.post(f'/api/training/plan/{self.dog.id}/evaluate/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_evaluate_dog_not_found(self):
        response = self.client.post(
            f'/api/training/plan/{uuid.uuid4()}/evaluate/',
            {'exercise_id': self.ex_sientate.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_evaluate_no_active_plan(self):
        response = self.client.post(
            f'/api/training/plan/{self.dog.id}/evaluate/',
            {'exercise_id': self.ex_sientate.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_evaluate_not_mastered(self):
        create_plan(self.dog, self.catalog['levels']['lvl1'],
                    [(self.ex_sientate, self.comida)])
        # Solo 1 sesión: no alcanza las 3 requeridas
        create_session(self.dog, self.ex_sientate, self.comida, success=True)
        response = self.client.post(
            f'/api/training/plan/{self.dog.id}/evaluate/',
            {'exercise_id': self.ex_sientate.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['exercise_mastered'])

    def test_evaluate_masters_and_unlocks_next_exercise(self):
        # Plan con 2 ejercicios; sientate dominado, echate no → nivel incompleto
        create_plan(self.dog, self.catalog['levels']['lvl1'],
                    [(self.ex_sientate, self.comida), (self.ex_echate, self.comida)])
        for _ in range(3):
            create_session(self.dog, self.ex_sientate, self.comida, success=True)

        response = self.client.post(
            f'/api/training/plan/{self.dog.id}/evaluate/',
            {'exercise_id': self.ex_sientate.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exercise_mastered'])
        self.assertFalse(response.data['level_upgraded'])
        self.assertIsNotNone(response.data['next_exercise_unlocked'])
        # 'llamado' es el siguiente ejercicio del nivel 1 no incluido aún
        self.assertEqual(response.data['next_exercise_unlocked']['name'], 'Llamado')

    def test_evaluate_completes_level_and_upgrades(self):
        # Plan con un único ejercicio dominado → nivel completo → sube a nivel 2
        create_plan(self.dog, self.catalog['levels']['lvl1'],
                    [(self.ex_sientate, self.comida)])
        for _ in range(3):
            create_session(self.dog, self.ex_sientate, self.comida, success=True)

        response = self.client.post(
            f'/api/training/plan/{self.dog.id}/evaluate/',
            {'exercise_id': self.ex_sientate.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['exercise_mastered'])
        self.assertTrue(response.data['level_upgraded'])
        self.assertEqual(response.data['new_level'], 'Nivel 2')


class LevelUpgradeOrderingTests(TestCase):
    """
    Regresión #1: el ascenso de nivel se decide por el número del nombre
    ('Nivel N+1'), no por el orden lexicográfico del id (que es un UUID).
    """

    def setUp(self):
        self.user = make_user()
        self.client = auth_client(self.user)
        # Ids deliberadamente "desordenados": el Nivel 1 tiene un id mayor
        # que el Nivel 2, así que ordenar por id daría el resultado incorrecto.
        self.lvl1 = TrainingLevels.objects.create(id='zzz-nivel', name='Nivel 1', description='')
        self.lvl2 = TrainingLevels.objects.create(id='aaa-nivel', name='Nivel 2', description='')
        self.comida = ReinforcementTypes.objects.create(id='ref-001', name='Comida')
        self.ex1 = Exercises.objects.create(
            id='ex-001', level=self.lvl1, name='Siéntate', difficulty=1, estimated_duration=10
        )
        Exercises.objects.create(
            id='ex-101', level=self.lvl2, name='Rastreo', difficulty=1, estimated_duration=10
        )
        Exercises.objects.create(
            id='ex-102', level=self.lvl2, name='Agility', difficulty=2, estimated_duration=10
        )
        self.dog = create_dog(self.user)
        create_plan(self.dog, self.lvl1, [(self.ex1, self.comida)])
        for _ in range(3):
            create_session(self.dog, self.ex1, self.comida, success=True)

    def test_upgrades_to_next_level_by_name_not_by_id(self):
        response = self.client.post(
            f'/api/training/plan/{self.dog.id}/evaluate/',
            {'exercise_id': self.ex1.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['level_upgraded'])
        self.assertEqual(response.data['new_level'], 'Nivel 2')

    def test_previous_level_kept_inactive_with_continuous_numbering(self):
        # Regresión #8: al subir de nivel, los ejercicios del nivel anterior
        # se conservan inactivos y los nuevos continúan la numeración.
        self.client.post(
            f'/api/training/plan/{self.dog.id}/evaluate/',
            {'exercise_id': self.ex1.id}, format='json',
        )
        plan = TrainingPlans.objects.get(dog=self.dog)
        old = TrainingPlanExercises.objects.get(training_plan=plan, exercise=self.ex1)
        self.assertFalse(old.active)  # conservado pero inactivo, no eliminado

        new_exercises = TrainingPlanExercises.objects.filter(training_plan=plan, active=True)
        self.assertEqual(new_exercises.count(), 2)  # los 2 del nuevo nivel
        # La numeración continúa: todos los nuevos tienen order_number > el viejo
        self.assertTrue(all(pe.order_number > old.order_number for pe in new_exercises))


class DominatedExerciseConfirmationTests(TestCase):
    """
    Regresión #2/Q2: un ejercicio marcado como dominado en el quiz se
    confirma con 1 sola sesión exitosa (poco esfuerzo). Si la última falla,
    debe repasarse con la regla normal (3 sesiones al 80%).
    """

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.ex = self.catalog['exercises']['sientate']
        self.comida = self.catalog['reinforcements']['comida']
        _, pes = create_plan(
            self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.comida)]
        )
        # Marcar el ejercicio como dominado en el quiz
        pes[0].dominated = True
        pes[0].save()

    def _evaluate(self):
        return self.client.post(
            f'/api/training/plan/{self.dog.id}/evaluate/',
            {'exercise_id': self.ex.id}, format='json',
        )

    def test_dominated_confirmed_with_single_success(self):
        create_session(self.dog, self.ex, self.comida, success=True)
        response = self._evaluate()
        self.assertTrue(response.data['exercise_mastered'])

    def test_dominated_needs_review_when_last_session_fails(self):
        # Le costó esfuerzo (falló): no se confirma, debe repasar como normal.
        create_session(self.dog, self.ex, self.comida, success=False)
        response = self._evaluate()
        self.assertFalse(response.data['exercise_mastered'])


class UpdateReinforcementTests(TestCase):
    """PUT /plan/<dog_id>/exercise/<plan_exercise_id>/reinforcement/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.plan, self.plan_exercises = create_plan(
            self.dog, self.catalog['levels']['lvl1'],
            [(self.catalog['exercises']['sientate'], self.catalog['reinforcements']['comida'])],
        )
        self.plan_exercise = self.plan_exercises[0]

    def _url(self, pe_id):
        return f'/api/training/plan/{self.dog.id}/exercise/{pe_id}/reinforcement/'

    def test_update_reinforcement_success(self):
        nueva = self.catalog['reinforcements']['pelota']
        response = self.client.put(
            self._url(self.plan_exercise.id),
            {'reinforcement_type_id': nueva.id}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.plan_exercise.refresh_from_db()
        self.assertEqual(self.plan_exercise.reinforcement_type_id, nueva.id)
        self.assertEqual(response.data['plan_exercise']['reinforcement_type']['name'], 'Pelota')

    def test_update_reinforcement_requires_id(self):
        response = self.client.put(self._url(self.plan_exercise.id), {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_reinforcement_not_found_reinforcement(self):
        response = self.client.put(
            self._url(self.plan_exercise.id),
            {'reinforcement_type_id': 'ref-inexistente'}, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_reinforcement_plan_exercise_not_found(self):
        response = self.client.put(
            self._url(str(uuid.uuid4())),
            {'reinforcement_type_id': self.catalog['reinforcements']['pelota'].id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_reinforcement_dog_not_found(self):
        response = self.client.put(
            f'/api/training/plan/{uuid.uuid4()}/exercise/{self.plan_exercise.id}/reinforcement/',
            {'reinforcement_type_id': self.catalog['reinforcements']['pelota'].id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
