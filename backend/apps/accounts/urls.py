"""
Fichier : apps/accounts/urls.py
Description : Routes d'authentification et de gestion des utilisateurs.
"""
from django.urls import path
from apps.accounts.views import RegisterView
from apps.accounts.views import RegisterView, CustomTokenObtainPairView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
]

