from django.urls import path
from . import views

urlpatterns = [
    path('<str:dog_id>/', views.list_sessions, name='list_sessions'),
    path('<str:dog_id>/create/', views.create_session, name='create_session'),
    path('<str:dog_id>/stats/', views.session_stats, name='session_stats'),
]