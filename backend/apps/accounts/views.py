"""
Fichier : apps/accounts/views.py
Description : Vues pour l'authentification et la gestion des comptes utilisateurs.
"""
from rest_framework import status, permissions, generics
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

User = get_user_model()

class RegisterView(APIView):
    """
    Endpoint : POST /api/auth/register/
    Permet l'inscription d'un nouvel utilisateur.
    """
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # On réutilise UserSerializer pour formater la réponse proprement
            response_serializer = UserSerializer(user)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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

class ThrottledTokenRefreshView(TokenRefreshView):
    """
    Endpoint : POST /api/auth/refresh/
    Rafraîchit l'access token à partir d'un refresh token valide.
    """

    permission_classes = [AllowAny]
    throttle_scope = "auth"