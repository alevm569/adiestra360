from django.urls import path
from . import views

urlpatterns = [
    path('levels/', views.list_levels, name='list_levels'),
    path('exercises/', views.list_exercises, name='list_exercises'),
    path('reinforcements/', views.list_reinforcements, name='list_reinforcements'),
    path('plan/<str:dog_id>/', views.get_active_plan, name='get_active_plan'),
    path('plan/<str:dog_id>/evaluate/', views.evaluate_progress, name='evaluate_progress'),
    path('plan/<str:dog_id>/exercise/<str:plan_exercise_id>/reinforcement/', views.update_exercise_reinforcement, name='update_reinforcement'),
    path('exercise/<str:exercise_id>/technique/<str:dog_id>/', views.exercise_technique, name='exercise_technique'),
]