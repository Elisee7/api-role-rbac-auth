"""
Fichier : apps/roles/urls.py
Description : Déclaration des routes pour le module rôles et permissions.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.roles.views import RoleViewSet, PermissionViewSet

router = DefaultRouter()
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')

urlpatterns = [
    path('', include(router.urls)),
]