"""
Fichier : apps/roles/permissions.py
Description : Classes de permission DRF pour le contrôle d'accès basé sur les rôles (RBAC).
"""
from rest_framework import permissions


class HasRolePermission(permissions.BasePermission):
    """
    Permission DRF dynamique qui vérifie si le rôle de l'utilisateur détient
    la permission requise définie au niveau de la vue (attribut `required_permission`).
    """

    def has_permission(self, request, view):
        # 1. Vérification de l'authentification de l'utilisateur
        if not request.user or not request.user.is_authenticated:
            return False

        # Les superutilisateurs (is_superuser) conservent tous les accès d'administration
        if request.user.is_superuser:
            return True

        # 2. Récupération de la permission requise définie dans la vue
        required_permission = getattr(view, 'required_permission', None)

        # Si aucune permission spécifique n'est exigée par la vue, l'accès est accordé à tout utilisateur authentifié
        if not required_permission:
            return True

        # 3. Vérification si l'utilisateur a un rôle associé
        if not request.user.role:
            return False

        # 4. Vérification si le rôle contient le code de permission requis
        return request.user.role.has_permission(required_permission)