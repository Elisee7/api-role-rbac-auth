"""
Fichier : apps/roles/serializers.py
Description : Sérialiseurs pour la gestion des rôles et des permissions (RBAC).
"""
from rest_framework import serializers
from apps.roles.models import Role, Permission


class PermissionSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la lecture des permissions.
    """
    class Meta:
        model = Permission
        fields = ('id', 'code', 'description', 'created_at')
        read_only_fields = fields


class RoleSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les opérations CRUD sur les rôles.
    Expose les permissions sous forme d'objets en lecture et accepte leurs IDs en écriture.
    """
    permissions_detail = PermissionSerializer(source='permissions', many=True, read_only=True)
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Role
        fields = ('id', 'name', 'description', 'permissions', 'permissions_detail', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')