"""
Fichier : apps/accounts/urls.py
Description : Routes d'authentification et de gestion des utilisateurs.
"""
from django.urls import path
from apps.accounts.views import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    UserAssignRoleView,
    UserMeView,
    ThrottledTokenRefreshView,
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='auth-register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='auth-login'),
    path('auth/refresh/', ThrottledTokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('users/<int:pk>/assign-role/', UserAssignRoleView.as_view(), name='user-assign-role'),
    path('users/me/', UserMeView.as_view(), name='user-me'),
]

