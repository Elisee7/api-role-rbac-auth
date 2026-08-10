"""
Fichier : apps/roles/models.py
Description : Modèles de données pour la gestion des rôles et des permissions (RBAC).
"""
from django.db import models


class Permission(models.Model):
    """
    Représente une permission granulaire dans le système (ex: 'users.read', 'roles.manage').
    """
    code = models.CharField(max_length=100, unique=True, verbose_name="Code permission")
    description = models.TextField(blank=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auth_permission_custom'
        verbose_name = 'Permission'
        verbose_name_plural = 'Permissions'
        ordering = ['code']

    def __str__(self):
        return self.code


class Role(models.Model):
    """
    Représente un rôle applicatif (ex: Admin, Gestionnaire, Utilisateur standard).
    """
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du rôle")
    description = models.TextField(blank=True, verbose_name="Description")
    permissions = models.ManyToManyField(
        Permission,
        related_name='roles',
        blank=True,
        verbose_name="Permissions associées"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'auth_role'
        verbose_name = 'Rôle'
        verbose_name_plural = 'Rôles'

    def __str__(self):
        return self.name

    def has_permission(self, permission_code: str) -> bool:
        """
        Vérifie si ce rôle contient une permission spécifique par son code.
        """
        return self.permissions.filter(code=permission_code).exists()
