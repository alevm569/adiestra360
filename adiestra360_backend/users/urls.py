from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    # Recuperación de contraseña: se pide un código y luego se confirma.
    path('password-reset/', views.password_reset_request, name='password_reset'),
    path('password-reset/confirm/', views.password_reset_confirm,
         name='password_reset_confirm'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('quiz/', views.quiz_questions, name='quiz'),
    # Renueva el access token con el refresh token (usado por el front).
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]