from django.urls import path
from . import views

urlpatterns = [
    path('<str:dog_id>/analyze/', views.analyze_and_recommend, name='analyze'),
    path('<str:dog_id>/history/', views.get_recommendations, name='recommendations_history'),
    path('<str:dog_id>/active/', views.get_active_recommendation, name='active_recommendation'),
]