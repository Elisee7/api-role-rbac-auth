"""
Fichier : apps/roles/views.py
Description : Vues API pour le CRUD des rôles et des permissions.
"""
from rest_framework import viewsets, permissions
from apps.roles.models import Role, Permission
from apps.roles.serializers import RoleSerializer, PermissionSerializer
from apps.roles.permissions import HasRolePermission


class RoleViewSet(viewsets.ModelViewSet):
    """
    Endpoint : /api/roles/
    Permet la gestion complète (CRUD) des rôles applicatifs.
    Réservé aux administrateurs (exige la permission 'roles.manage').
    """
    queryset = Role.objects.all().order_by('id')
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, HasRolePermission]
    required_permission = 'roles.manage'


class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint : /api/permissions/
    Permet la consultation en lecture seule des permissions disponibles dans le système.
    """
    queryset = Permission.objects.all().order_by('code')
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, HasRolePermission]
    required_permission = 'roles.manage'
