"""
Fichier : apps/accounts/views.py
Description : Vues pour l'authentification et la gestion des comptes utilisateurs.
"""
from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.accounts.serializers import ( RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer, 
                                       LogoutSerializer, UserAssignRoleSerializer, UserDetailSerializer,
                                       )
from apps.roles.models import Role
from apps.roles.permissions import HasRolePermission

User = get_user_model()

class RegisterView(APIView):
    """
    Endpoint : POST /api/auth/register/
    Permet l'inscription d'un nouvel utilisateur (accès public).
    """
    permission_classes = [permissions.AllowAny]

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

class LogoutView(APIView):
    """
    Endpoint : POST /api/auth/logout/
    Permet à un utilisateur authentifié de se déconnecter en invalidant
    son refresh token via la blacklist.
    
    Exige un Access Token valide dans les headers Authorization (Bearer <token>).
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Reçoit le refresh token dans le corps de la requête et le révoque.
        """
        serializer = LogoutSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Déconnexion réussie. Le token a été révoqué."},
                status=status.HTTP_205_RESET_CONTENT
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 3. Récupération et assignation du rôle
        role_id = serializer.validated_data['role_id']
        role = Role.objects.get(id=role_id)
        
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

