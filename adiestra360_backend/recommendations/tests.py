from django.test import TestCase
from rest_framework import status
import uuid

from testkit import (
    create_catalog, make_user, auth_client, create_dog,
    create_plan, create_session,
)
from recommendations.models import AiRecommendations


def make_recommendation(dog, previous, recommended, reason='motivo'):
    return AiRecommendations.objects.create(
        id=str(uuid.uuid4()), dog=dog,
        previous_strategy=previous, recommended_strategy=recommended,
        reason=reason,
    )


class FindBestReinforcementPurityTests(TestCase):
    """
    Regresión #2: find_best_reinforcement no debe mutar el diccionario
    global CATEGORY_REINFORCEMENT_PRIORITY (estado compartido entre requests).
    """

    def test_disciplina_branch_does_not_mutate_global_priority(self):
        import copy
        from recommendations.views import (
            find_best_reinforcement, CATEGORY_REINFORCEMENT_PRIORITY,
        )
        snapshot = copy.deepcopy(CATEGORY_REINFORCEMENT_PRIORITY)
        # La rama 'disciplina' ajusta la prioridad según la energía del perro.
        for energy in ['alto', 'medio', 'bajo']:
            find_best_reinforcement({}, 'ref-x', 'disciplina', energy)
        self.assertEqual(CATEGORY_REINFORCEMENT_PRIORITY, snapshot)


class CurrentReinforcementTests(TestCase):
    """
    Regresión #7: get_current_reinforcement toma el refuerzo de un ejercicio
    ACTIVO del plan, no de uno inactivo (de un nivel ya superado).
    """

    def test_prefers_active_exercise_reinforcement(self):
        from recommendations.views import get_current_reinforcement
        catalog = create_catalog()
        user = make_user()
        dog = create_dog(user)
        comida = catalog['reinforcements']['comida']
        pelota = catalog['reinforcements']['pelota']
        ex1 = catalog['exercises']['sientate']
        ex2 = catalog['exercises']['echate']
        _, pes = create_plan(
            dog, catalog['levels']['lvl1'], [(ex1, comida), (ex2, pelota)]
        )
        # ex1/comida queda inactivo (nivel anterior); ex2/pelota activo
        pes[0].active = False
        pes[0].save()

        reinforcement, level = get_current_reinforcement(str(dog.id))
        self.assertEqual(reinforcement.id, pelota.id)
        self.assertEqual(level, 1)


class AnalyzeAndRecommendTests(TestCase):
    """POST /api/recommendations/<dog_id>/analyze/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user, energy_level='medio')
        self.ex = self.catalog['exercises']['sientate']
        self.comida = self.catalog['reinforcements']['comida']
        self.pelota = self.catalog['reinforcements']['pelota']

    def test_analyze_needs_minimum_sessions(self):
        create_plan(self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.comida)])
        create_session(self.dog, self.ex, self.comida, success=False)
        response = self.client.post(f'/api/recommendations/{self.dog.id}/analyze/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['recommendation'])
        self.assertIn('al menos', response.data['message'])

    def test_analyze_recommends_better_reinforcement(self):
        create_plan(self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.comida)])
        # Refuerzo actual (comida): 25% de éxito
        create_session(self.dog, self.ex, self.comida, success=True, response_time=12)
        for _ in range(3):
            create_session(self.dog, self.ex, self.comida, success=False, response_time=15)
        # Alternativa (pelota): 100% de éxito y respuesta rápida
        for _ in range(3):
            create_session(self.dog, self.ex, self.pelota, success=True, response_time=3)

        response = self.client.post(f'/api/recommendations/{self.dog.id}/analyze/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['recommendation'])
        self.assertEqual(
            response.data['recommendation']['recommended_strategy_name'], 'Pelota'
        )
        self.assertTrue(AiRecommendations.objects.filter(dog=self.dog).exists())

    def test_analyze_acceptable_performance_no_recommendation(self):
        create_plan(self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.comida)])
        for _ in range(3):
            create_session(self.dog, self.ex, self.comida, success=True, response_time=3)
        response = self.client.post(f'/api/recommendations/{self.dog.id}/analyze/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['recommendation'])

    def test_analyze_no_active_plan(self):
        # 3 sesiones pero sin plan activo
        for _ in range(3):
            create_session(self.dog, self.ex, self.comida, success=False)
        response = self.client.post(f'/api/recommendations/{self.dog.id}/analyze/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['recommendation'])

    def test_analyze_dog_not_found(self):
        response = self.client.post(f'/api/recommendations/{uuid.uuid4()}/analyze/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_analyze_unauthenticated(self):
        self.client.credentials()
        response = self.client.post(f'/api/recommendations/{self.dog.id}/analyze/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RecommendationHistoryTests(TestCase):
    """GET /api/recommendations/<dog_id>/history/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.comida = self.catalog['reinforcements']['comida']
        self.pelota = self.catalog['reinforcements']['pelota']

    def test_history_returns_recommendations(self):
        make_recommendation(self.dog, self.comida, self.pelota)
        make_recommendation(self.dog, self.pelota, self.comida)
        response = self.client.get(f'/api/recommendations/{self.dog.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_history_empty(self):
        response = self.client.get(f'/api/recommendations/{self.dog.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_history_dog_not_found(self):
        response = self.client.get(f'/api/recommendations/{uuid.uuid4()}/history/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_history_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(f'/api/recommendations/{self.dog.id}/history/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ActiveRecommendationTests(TestCase):
    """GET /api/recommendations/<dog_id>/active/"""

    def setUp(self):
        self.catalog = create_catalog()
        self.user = make_user()
        self.client = auth_client(self.user)
        self.dog = create_dog(self.user)
        self.ex = self.catalog['exercises']['sientate']
        self.comida = self.catalog['reinforcements']['comida']
        self.pelota = self.catalog['reinforcements']['pelota']

    def test_active_returns_pending_recommendation(self):
        # Plan usa comida; la recomendación sugiere pelota → aún no aplicada
        create_plan(self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.comida)])
        make_recommendation(self.dog, self.comida, self.pelota)
        response = self.client.get(f'/api/recommendations/{self.dog.id}/active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['active_recommendation'])
        self.assertEqual(
            response.data['active_recommendation']['recommended_strategy_name'], 'Pelota'
        )

    def test_active_none_when_no_recommendation(self):
        create_plan(self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.comida)])
        response = self.client.get(f'/api/recommendations/{self.dog.id}/active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['active_recommendation'])

    def test_active_none_when_already_applied(self):
        # El plan ya usa pelota, que es justo lo recomendado → aplicada
        create_plan(self.dog, self.catalog['levels']['lvl1'], [(self.ex, self.pelota)])
        make_recommendation(self.dog, self.comida, self.pelota)
        response = self.client.get(f'/api/recommendations/{self.dog.id}/active/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['active_recommendation'])

    def test_active_dog_not_found(self):
        response = self.client.get(f'/api/recommendations/{uuid.uuid4()}/active/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_active_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(f'/api/recommendations/{self.dog.id}/active/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
