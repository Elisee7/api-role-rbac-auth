"""
Fichier : apps/accounts/views.py
Description : Vues pour l'authentification et la gestion des comptes utilisateurs.
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.accounts.serializers import ( RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer, 
                                       LogoutSerializer)



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