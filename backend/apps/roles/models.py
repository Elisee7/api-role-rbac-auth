"""
Fichier : apps/roles/models.py
Description : Modèles de données pour la gestion des rôles et des permissions (RBAC).
"""
from django.utils import timezone
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
    name = models.CharField(max_length=50, unique=True, verbose_name="Nom du rôle")
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField('Permission', related_name='roles', blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def has_permission(self, permission_code):
        """
        Vérifie si ce rôle possède la permission via son code.
        Optimisé en mémoire si 'permissions' a été préchargé via prefetch_related.
        """
        # Si permissions est déjà chargé en mémoire (prefetch)
        if hasattr(self, '_prefetched_objects_cache') and 'permissions' in self._prefetched_objects_cache:
            return any(perm.code == permission_code for perm in self.permissions.all())

        # Sinon, exécution d'une requête optimisée en base de données
        return self.permissions.filter(code=permission_code).exists()