"""
Fichier : apps/accounts/urls.py
Description : Routes d'authentification et de gestion des utilisateurs.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from apps.accounts.views import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    UserAssignRoleView,
    UserMeView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('users/<int:pk>/assign-role/', UserAssignRoleView.as_view(), name='user-assign-role'),
    path('users/me/', UserMeView.as_view(), name='user-me'),
]

