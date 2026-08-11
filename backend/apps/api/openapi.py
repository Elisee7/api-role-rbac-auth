"""
Fichier : apps/api/openapi.py
Description : Composants OpenAPI réutilisables (ticket AUTH-031).

Centralise les réponses d'erreur standard et le schéma "detail" partagé
afin d'éviter la duplication entre les endpoints (principe DRY).

Ce module ne contient AUCUNE logique métier : uniquement de la
déclaration de schéma consommée par drf-spectacular.
"""
from rest_framework import serializers
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes


# ---------------------------------------------------------------------------
# Schéma générique {"detail": "..."}
# C'est la forme renvoyée par DRF pour les erreurs 401 / 403 / 404,
# et aussi par la déconnexion (succès 200). Un seul composant réutilisé.
# ---------------------------------------------------------------------------
DetailResponse = inline_serializer(
    name="DetailResponse",
    fields={
        "detail": serializers.CharField(help_text="Message descriptif."),
    },
)


# ---------------------------------------------------------------------------
# Réponses d'erreur réutilisables (mutualisées sur tous les endpoints).
# Les exemples sont issus des cas réels couverts par la suite de tests.
# ---------------------------------------------------------------------------

# 400 : la forme varie selon le champ rejeté ({"champ": ["erreur"]})
# -> on utilise un objet générique plutôt qu'un sérialiseur rigide.
RESPONSE_400_BAD_REQUEST = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Requête invalide : un ou plusieurs champs sont rejetés.",
    examples=[
        OpenApiExample(
            "Champ invalide",
            value={"field_name": ["Ce champ est invalide."]},
        ),
    ],
)

# 401 : token absent, invalide ou expiré / identifiants incorrects.
RESPONSE_401_UNAUTHORIZED = OpenApiResponse(
    response=DetailResponse,
    description="Non authentifié : token absent, invalide ou expiré.",
    examples=[
        OpenApiExample(
            "Token invalide",
            value={"detail": "Given token not valid for any token type"},
        ),
    ],
)

# 403 : le rôle de l'utilisateur ne possède pas la permission requise.
RESPONSE_403_FORBIDDEN = OpenApiResponse(
    response=DetailResponse,
    description="Accès refusé : permission insuffisante pour ce rôle.",
    examples=[
        OpenApiExample(
            "Permission manquante",
            value={"detail": "Permission requise manquante : 'roles.manage'."},
        ),
    ],
)

# 404 : ressource introuvable.
RESPONSE_404_NOT_FOUND = OpenApiResponse(
    response=DetailResponse,
    description="Ressource introuvable.",
    examples=[
        OpenApiExample("Introuvable", value={"detail": "Not found."}),
    ],
)

# ---------------------------------------------------------------------------
# 429 : trop de requêtes.
# Réponse renvoyée lorsque la limite de débit configurée pour le scope
# d'authentification est dépassée (AUTH-033).
# La valeur réelle est pilotée par la variable d'environnement
# THROTTLE_AUTH_RATE, afin de ne pas la coder en dur.
# ---------------------------------------------------------------------------
RESPONSE_429_TOO_MANY_REQUESTS = OpenApiResponse(
    response=DetailResponse,
    description=(
        "Trop de requêtes : la limite de débit autorisée est dépassée."
    ),
    examples=[
        OpenApiExample(
            "Limite dépassée",
            value={"detail": "Request was throttled."},
        ),
    ],
)