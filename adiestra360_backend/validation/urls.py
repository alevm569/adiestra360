from django.urls import path
from . import views

urlpatterns = [
    path('survey/', views.survey, name='validation_survey'),
    path('metrics/', views.metrics, name='validation_metrics'),
]
