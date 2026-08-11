"""
Fichier : apps/accounts/views.py
Description : Vues pour l'authentification et la gestion des comptes utilisateurs.
"""
from rest_framework import status, permissions, generics, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.accounts.serializers import ( RegisterSerializer, UserProfileUpdateSerializer, UserSerializer, CustomTokenObtainPairSerializer, 
                                       LogoutSerializer, UserAssignRoleSerializer, UserDetailSerializer,
                                       )
from apps.roles.models import Role
from apps.roles.permissions import HasRolePermission
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiExample,
    inline_serializer,
)
from apps.api.openapi import (
    RESPONSE_400_BAD_REQUEST,
    RESPONSE_401_UNAUTHORIZED,
    RESPONSE_403_FORBIDDEN,
    RESPONSE_404_NOT_FOUND,
    DetailResponse,
)

User = get_user_model()

class RegisterView(APIView):
    """
    Endpoint : POST /api/auth/register/
    Permet l'inscription d'un nouvel utilisateur.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    # AUTH-031 : enrichissement du schéma OpenAPI.
    @extend_schema(
        tags=["Auth"],
        auth=[],
        summary="Inscription d'un nouvel utilisateur",
        description=(
            "Crée un compte avec un email unique et un mot de passe conforme "
            "à la politique de sécurité. Le rôle par défaut 'USER' est "
            "attribué automatiquement."
        ),
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: RESPONSE_400_BAD_REQUEST,
        },
        examples=[
            # Exemple REQUÊTE (pas de status_codes → appliqué au body d'entrée)
            OpenApiExample(
                "Requête valide",
                value={
                    "email": "jane.doe@example.com",
                    "username": "janedoe",
                    "password": "StrongPassword123!",
                },
                request_only=True,
            ),
            # Exemple RÉPONSE (status_codes → appliqué à la sortie 201)
            OpenApiExample(
                "Réponse 201",
                value={
                    "id": 1,
                    "email": "jane.doe@example.com",
                    "username": "janedoe",
                    "first_name": "",
                    "last_name": "",
                    "role": "USER",
                    "date_joined": "2026-08-11T09:00:00Z",
                },
                status_codes=["201"],
            ),
        ],
    )

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # On réutilise UserSerializer pour formater la réponse proprement
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# AUTH-031 : le champ `user` étant injecté dynamiquement dans validate(),
# la réponse 200 est déclarée explicitement via inline_serializer.
# On utilise @extend_schema_view car la méthode `post` est héritée de
# TokenObtainPairView (pas de méthode locale à décorer).
@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Connexion — émission des tokens JWT",
        description=(
            "Authentifie l'utilisateur via son email et son mot de passe, "
            "puis retourne un couple access token / refresh token ainsi que "
            "le profil utilisateur. Le rôle est injecté dans le payload du "
            "token (claim 'role')."
        ),
        # Le schéma de requête (email + password) est déduit du sérialiseur,
        # car USERNAME_FIELD = 'email' sur le modèle CustomUser.
        request=CustomTokenObtainPairSerializer,
        responses={
            200: inline_serializer(
                name="LoginResponse",
                fields={
                    "access": serializers.CharField(help_text="Access token JWT (15 min)."),
                    "refresh": serializers.CharField(help_text="Refresh token JWT (7 jours)."),
                    "user": UserSerializer(),
                },
            ),
            401: RESPONSE_401_UNAUTHORIZED,
        },
        examples=[
            # Exemple REQUÊTE (pas de status_codes → appliqué au body d'entrée)
            OpenApiExample(
                "Identifiants valides",
                value={
                    "email": "jane.doe@example.com",
                    "password": "StrongPassword123!",
                },
                request_only=True,
            ),
            # Exemple RÉPONSE 200 (status_codes → appliqué à la sortie 200)
            OpenApiExample(
                "Connexion réussie",
                value={
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "user": {
                        "id": 1,
                        "email": "jane.doe@example.com",
                        "username": "janedoe",
                        "first_name": "",
                        "last_name": "",
                        "role": "USER",
                        "date_joined": "2026-08-11T09:00:00Z",
                    },
                },
                status_codes=["200"],
            ),
            # Exemple RÉPONSE 401 : identifiants invalides (spécifique au login)
            OpenApiExample(
                "Identifiants invalides",
                value={
                    "detail": "No active account found with the given credentials",
                },
                status_codes=["401"],
            ),
        ],
    )
)
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint : POST /api/auth/login/
    Permet la connexion d'un utilisateur et l'émission des tokens JWT (access + refresh).
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

class LogoutView(APIView):
    """
    Endpoint : POST /api/auth/logout/
    Permet à un utilisateur authentifié de se déconnecter en invalidant
    son refresh token via la blacklist.
    Exige un Access Token valide dans les headers Authorization (Bearer <token>).
    """
    serializer_class = LogoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "auth"

    # AUTH-031 : enrichissement du schéma OpenAPI.
    @extend_schema(
        tags=["Auth"],
        summary="Déconnexion — révocation du refresh token",
        description=(
            "Invalide le refresh token fourni en l'ajoutant à la liste noire "
            "(blacklist). Exige un Access Token valide dans l'en-tête "
            "Authorization (Bearer <token>). Une fois révoqué, ce refresh "
            "token ne peut plus servir à rafraîchir la session."
        ),
        request=LogoutSerializer,
        responses={
            200: DetailResponse,
            400: RESPONSE_400_BAD_REQUEST,
            401: RESPONSE_401_UNAUTHORIZED,
        },
        examples=[
            # Exemple REQUÊTE (pas de status_codes → appliqué au body d'entrée)
            OpenApiExample(
                "Requête valide",
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                request_only=True,
            ),
            # Exemple RÉPONSE 200 : confirmation de déconnexion
            OpenApiExample(
                "Déconnexion réussie",
                value={
                    "detail": "Déconnexion réussie. Le token a été révoqué.",
                },
                status_codes=["200"],
            ),
            # Exemple RÉPONSE 400 : refresh token invalide ou déjà révoqué
            OpenApiExample(
                "Refresh token invalide",
                value={
                    "refresh": ["Token invalide ou déjà révoqué."],
                },
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        """
        Reçoit le refresh token dans le corps de la requête et le révoque.
        """
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Déconnexion réussie. Le token a été révoqué."},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class UserAssignRoleView(generics.GenericAPIView):
    """
    Endpoint : POST /api/users/<id>/assign-role/
    Permet à un administrateur d'assigner un rôle à un utilisateur.
    Exige la permission 'roles.manage'.
    """
    permission_classes = [permissions.IsAuthenticated, HasRolePermission]
    required_permission = 'roles.manage'
    serializer_class = UserAssignRoleSerializer

    # AUTH-031 : la réponse 200 est construite manuellement dans la vue
    # (message + profil utilisateur), on la déclare donc via inline_serializer.
    @extend_schema(
        tags=["Users"],
        summary="Assigner un rôle à un utilisateur",
        description=(
            "Attribue un rôle à l'utilisateur cible identifié par son id. "
            "Réservé aux administrateurs (permission 'roles.manage'). La "
            "réponse contient un message de confirmation ainsi que le profil "
            "mis à jour de l'utilisateur cible."
        ),
        request=UserAssignRoleSerializer,
        responses={
            200: inline_serializer(
                name="AssignRoleResponse",
                fields={
                    "message": serializers.CharField(help_text="Message de confirmation."),
                    "user": UserDetailSerializer(),
                },
            ),
            400: RESPONSE_400_BAD_REQUEST,
            401: RESPONSE_401_UNAUTHORIZED,
            403: RESPONSE_403_FORBIDDEN,
            404: RESPONSE_404_NOT_FOUND,
        },
        examples=[
            # Exemple REQUÊTE (pas de status_codes → appliqué au body d'entrée)
            OpenApiExample(
                "Requête valide",
                value={"role_id": 2},
                request_only=True,
            ),
            # Exemple RÉPONSE 200 : rôle assigné + profil à jour
            OpenApiExample(
                "Rôle assigné",
                value={
                    "message": "Rôle 'MANAGER' assigné avec succès à l'utilisateur 'targetuser'.",
                    "user": {
                        "id": 3,
                        "email": "target@example.com",
                        "username": "targetuser",
                        "first_name": "",
                        "last_name": "",
                        "role": {
                            "id": 2,
                            "name": "MANAGER",
                            "description": "Gestionnaire",
                            "permissions": [1, 2, 5, 6],
                            "permissions_detail": [
                                {"id": 1, "code": "users.read", "description": "Consulter la liste/détails des utilisateurs", "created_at": "2026-08-05T00:00:00Z"},
                                {"id": 2, "code": "users.write", "description": "Créer et modifier des utilisateurs", "created_at": "2026-08-05T00:00:00Z"},
                                {"id": 5, "code": "profile.read", "description": "Consulter son propre profil", "created_at": "2026-08-05T00:00:00Z"},
                                {"id": 6, "code": "profile.write", "description": "Modifier son propre profil", "created_at": "2026-08-05T00:00:00Z"},
                            ],
                            "created_at": "2026-08-05T00:00:00Z",
                            "updated_at": "2026-08-05T00:00:00Z",
                        },
                        "is_active": True,
                        "date_joined": "2026-08-11T09:00:00Z",
                    },
                },
                request_only=True,
                status_codes=["200"],
            ),
            # Exemple RÉPONSE 400 : role_id inexistant (validate_role_id)
            OpenApiExample(
                "Rôle inexistant",
                value={"role_id": ["Le rôle spécifié n'existe pas."]},
                request_only=True,
                status_codes=["400"],
            ),
        ],
    )
    def post(self, request, pk=None):
        # 1. Récupération de l'utilisateur cible (404 si non trouvé)
        target_user = get_object_or_404(User, pk=pk)

        # 2. Validation des données transmises
        #    (le sérialiseur vérifie déjà l'existence du role_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 3. Récupération et assignation du rôle
        #    (get_object_or_404 retourne un 404 propre si le rôle
        #     venait à être supprimé entre la validation et cet appel)
        role_id = serializer.validated_data['role_id']
        role = get_object_or_404(Role, id=role_id)
        
        target_user.role = role
        target_user.save()

        # 4. Réponse avec le profil utilisateur mis à jour
        return Response(
            {
                "message": f"Rôle '{role.name}' assigné avec succès à l'utilisateur '{target_user.username}'.",
                "user": UserDetailSerializer(target_user).data
            },
            status=status.HTTP_200_OK
        )

# AUTH-031 : le sérialiseur varie selon la méthode (get_serializer_class),
# on annote donc `get` et `patch` séparément via @extend_schema_view.
@extend_schema_view(
    get=extend_schema(
        tags=["Users"],
        summary="Consulter son profil",
        description=(
            "Retourne les informations de l'utilisateur authentifié, y "
            "compris son rôle (objet détaillé). Exige un Access Token "
            "valide dans l'en-tête Authorization."
        ),
        responses={
            200: UserDetailSerializer,
            401: RESPONSE_401_UNAUTHORIZED,
        },
        examples=[
            # Exemple RÉPONSE 200 : profil avec rôle imbriqué (RoleSerializer)
            OpenApiExample(
                "Profil récupéré",
                value={
                    "id": 1,
                    "email": "jane.doe@example.com",
                    "username": "janedoe",
                    "first_name": "Jane",
                    "last_name": "Doe",
                    "role": {
                        "id": 3,
                        "name": "USER",
                        "description": "Utilisateur standard",
                        "permissions": [5, 6],
                        "permissions_detail": [
                            {
                                "id": 5,
                                "code": "profile.read",
                                "description": "Consulter son propre profil",
                                "created_at": "2026-08-05T00:00:00Z",
                            },
                            {
                                "id": 6,
                                "code": "profile.write",
                                "description": "Modifier son propre profil",
                                "created_at": "2026-08-05T00:00:00Z",
                            },
                        ],
                        "created_at": "2026-08-05T00:00:00Z",
                        "updated_at": "2026-08-05T00:00:00Z",
                    },
                    "is_active": True,
                    "date_joined": "2026-08-11T09:00:00Z",
                },
                status_codes=["200"],
            ),
        ],
    ),
    patch=extend_schema(
        tags=["Users"],
        summary="Mettre à jour son profil",
        description=(
            "Met à jour les champs éditables du profil de l'utilisateur "
            "authentifié (first_name, last_name, username). Les champs "
            "sensibles (email, rôle) ne sont pas modifiables via cet "
            "endpoint. Exige un Access Token valide."
        ),
        request=UserProfileUpdateSerializer,
        responses={
            200: UserProfileUpdateSerializer,
            400: RESPONSE_400_BAD_REQUEST,
            401: RESPONSE_401_UNAUTHORIZED,
        },
        examples=[
            # Exemple REQUÊTE (pas de status_codes → appliqué au body d'entrée)
            OpenApiExample(
                "Mise à jour du nom",
                value={
                    "first_name": "Jane",
                    "last_name": "Smith",
                },
                request_only=True,
            ),
            # Exemple RÉPONSE 200 : profil mis à jour
            OpenApiExample(
                "Profil mis à jour",
                value={
                    "first_name": "Jane",
                    "last_name": "Smith",
                    "username": "janedoe",
                },
                status_codes=["200"],
            ),
            # Exemple RÉPONSE 400 : username déjà utilisé (validate_username)
            OpenApiExample(
                "Username déjà utilisé",
                value={
                    "username": ["Ce nom d'utilisateur est déjà utilisé."],
                },
                status_codes=["400"],
            ),
        ],
    ),
)
class UserMeView(generics.RetrieveUpdateAPIView):
    """
    Endpoint : GET / PATCH /api/users/me/
    Permet à l'utilisateur authentifié de consulter et de modifier son profil.
    Exige un Access Token valide.
    """
    http_method_names = ["get", "patch", "head", "options"]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Récupère directement l'utilisateur lié au Token JWT
        return self.request.user

    def get_serializer_class(self):
        """
        Sélectionne le sérialiseur adapté selon la méthode HTTP.
        """
        if self.request.method == "PATCH":
            return UserProfileUpdateSerializer
        return UserDetailSerializer

# AUTH-031 : la méthode `post` est héritée de TokenRefreshView,
# on utilise donc @extend_schema_view pour l'annoter sans la redéfinir.
# La réponse 200 est déclarée explicitement car la rotation renvoie
# un NOUVEAU refresh token (absent du schéma par défaut du sérialiseur).
@extend_schema_view(
    post=extend_schema(
        tags=["Auth"],
        summary="Rafraîchissement des tokens JWT (avec rotation)",
        description=(
            "Émet un nouvel access token à partir d'un refresh token valide. "
            "La rotation est activée : un nouveau refresh token est retourné "
            "et l'ancien est immédiatement invalidé (blacklist). Un refresh "
            "token révoqué, expiré ou invalide est rejeté avec un statut 401."
        ),
        # Le schéma de requête ({"refresh": ...}) est déduit du sérialiseur SimpleJWT.
        request=TokenRefreshSerializer,
        responses={
            200: inline_serializer(
                name="TokenRefreshResponse",
                fields={
                    "access": serializers.CharField(help_text="Nouvel access token (15 min)."),
                    "refresh": serializers.CharField(help_text="Nouveau refresh token après rotation (7 jours)."),
                },
            ),
            401: RESPONSE_401_UNAUTHORIZED,
        },
        examples=[
            # Exemple REQUÊTE (pas de status_codes → appliqué au body d'entrée)
            OpenApiExample(
                "Refresh token valide",
                value={
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                request_only=True,
            ),
            # Exemple RÉPONSE 200 (status_codes → appliqué à la sortie 200)
            OpenApiExample(
                "Rotation réussie",
                value={
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                },
                request_only=True,
                status_codes=["200"],
            ),
        ],
    )
)
class ThrottledTokenRefreshView(TokenRefreshView):
    """
    Endpoint : POST /api/auth/refresh/
    Rafraîchit l'access token à partir d'un refresh token valide.
    """
    permission_classes = [AllowAny]
    throttle_scope = "auth"