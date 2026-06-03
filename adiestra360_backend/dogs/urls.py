from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_dogs, name='list_dogs'),
    path('create/', views.create_dog_profile, name='create_dog'),
    path('<str:dog_id>/', views.dog_detail, name='dog_detail'),
    path('<str:dog_id>/update/', views.update_dog, name='update_dog'),
]