from django.urls import path
from . import views

urlpatterns = [
    path('achievements/', views.list_achievements, name='list_achievements'),
    path('my-achievements/', views.user_achievements, name='user_achievements'),
    path('stats/', views.user_stats, name='user_stats'),
    path('dashboard/<str:dog_id>/', views.dashboard, name='dashboard'),
]