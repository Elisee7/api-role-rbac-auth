"""
Fichier : apps/roles/views.py
Description : Vues API pour le CRUD des rôles et des permissions.
"""
from rest_framework import viewsets, permissions
from apps.roles.models import Role, Permission
from apps.roles.serializers import RoleSerializer, PermissionSerializer
from apps.roles.permissions import HasRolePermission
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample

from apps.api.openapi import (
    RESPONSE_400_BAD_REQUEST,
    RESPONSE_401_UNAUTHORIZED,
    RESPONSE_403_FORBIDDEN,
    RESPONSE_404_NOT_FOUND,
)

# ---------------------------------------------------------------------------
# AUTH-031 : réponses d'erreur mutualisées pour les endpoints RBAC.
#   401 -> token absent/invalide     403 -> rôle insuffisant
#   404 -> ressource introuvable     400 -> corps de requête invalide
# Les exemples de ces erreurs sont déjà portés par les OpenApiResponse
# réutilisables (apps/api/openapi.py), pas besoin de les répéter ici.
# ---------------------------------------------------------------------------
_ERRORS_COLLECTION = {
    401: RESPONSE_401_UNAUTHORIZED,
    403: RESPONSE_403_FORBIDDEN,
}
_ERRORS_ITEM = {
    401: RESPONSE_401_UNAUTHORIZED,
    403: RESPONSE_403_FORBIDDEN,
    404: RESPONSE_404_NOT_FOUND,
}
_ERRORS_WRITE = {
    400: RESPONSE_400_BAD_REQUEST,
    401: RESPONSE_401_UNAUTHORIZED,
    403: RESPONSE_403_FORBIDDEN,
}

# Variante pour les opérations sur un item (update, partial_update, delete)
_ERRORS_WRITE_ITEM = {
    **_ERRORS_WRITE,
    404: RESPONSE_404_NOT_FOUND,
}


@extend_schema_view(
    list=extend_schema(
        tags=["Roles"],
        summary="Lister les rôles",
        description=(
            "Retourne la liste de tous les rôles applicatifs. Réservé aux "
            "administrateurs (permission 'roles.manage')."
        ),
        responses={200: RoleSerializer(many=True), **_ERRORS_COLLECTION},
    ),
    create=extend_schema(
        tags=["Roles"],
        summary="Créer un rôle",
        description=(
            "Crée un nouveau rôle avec ses permissions associées. Réservé "
            "aux administrateurs."
        ),
        responses={201: RoleSerializer, **_ERRORS_WRITE},
        examples=[
            # Exemple REQUÊTE (pas de status_codes → appliqué au body d'entrée)
            OpenApiExample(
                "Création du rôle MANAGER",
                value={
                    "name": "MANAGER",
                    "description": "Gestionnaire",
                    "permissions": [1, 2, 5, 6],
                },
            ),
            # Exemple RÉPONSE 201 : rôle créé avec ses permissions détaillées
            OpenApiExample(
                "Rôle créé",
                value={
                    "id": 2,
                    "name": "MANAGER",
                    "description": "Gestionnaire",
                    "permissions": [1, 2, 5, 6],
                    "permissions_detail": [
                        {"id": 1, "code": "users.read", "description": "Consulter la liste/détails des utilisateurs", "created_at": "2026-08-05T00:00:00Z"},
                        {"id": 2, "code": "users.write", "description": "Créer et modifier des utilisateurs", "created_at": "2026-08-05T00:00:00Z"},
                    ],
                    "created_at": "2026-08-11T09:00:00Z",
                    "updated_at": "2026-08-11T09:00:00Z",
                },
                status_codes=["201"],
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=["Roles"],
        summary="Détail d'un rôle",
        description="Retourne le détail d'un rôle par son identifiant. Réservé aux administrateurs.",
        responses={200: RoleSerializer, **_ERRORS_ITEM},
    ),
    update=extend_schema(
        tags=["Roles"],
        summary="Modifier un rôle (remplacement complet)",
        description="Remplace l'ensemble des champs d'un rôle. Réservé aux administrateurs.",
        responses={200: RoleSerializer, **_ERRORS_WRITE_ITEM},
    ),
    partial_update=extend_schema(
        tags=["Roles"],
        summary="Modifier un rôle (partiel)",
        description="Met à jour partiellement les champs d'un rôle. Réservé aux administrateurs.",
        responses={200: RoleSerializer, **_ERRORS_WRITE_ITEM},
    ),
    destroy=extend_schema(
        tags=["Roles"],
        summary="Supprimer un rôle",
        description=(
            "Supprime un rôle. Les utilisateurs associés auront leur champ "
            "role mis à null (on_delete=SET_NULL). Réservé aux administrateurs."
        ),
        responses={204: None, **_ERRORS_ITEM},
    ),
)
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


@extend_schema_view(
    list=extend_schema(
        tags=["Roles"],
        summary="Lister les permissions",
        description=(
            "Retourne la liste de toutes les permissions disponibles dans le "
            "système. Réservé aux administrateurs (permission 'roles.manage')."
        ),
        responses={200: PermissionSerializer(many=True), **_ERRORS_COLLECTION},
        examples=[
            # Réponse many=True : drf-spectacular enveloppe automatiquement la
            # valeur dans un tableau. On fournit donc UN SEUL objet (et non un
            # tableau) pour obtenir un tableau simple [{...}] à l'affichage.
            OpenApiExample(
                "Liste de permissions",
                value={
                    "id": 4,
                    "code": "roles.manage",
                    "description": "Gérer les rôles et permissions",
                    "created_at": "2026-08-05T00:00:00Z",
                },
                status_codes=["200"],
            ),
        ],
    ),
    retrieve=extend_schema(
        tags=["Roles"],
        summary="Détail d'une permission",
        description="Retourne le détail d'une permission par son identifiant. Réservé aux administrateurs.",
        responses={200: PermissionSerializer, **_ERRORS_ITEM},
    ),
)
class PermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint : /api/permissions/
    Permet la consultation en lecture seule des permissions disponibles dans le système.
    """
    queryset = Permission.objects.all().order_by('code')
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, HasRolePermission]
    required_permission = 'roles.manage'
