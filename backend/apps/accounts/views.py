"""
Fichier : apps/accounts/views.py
Description : Vues pour l'authentification et la gestion des comptes utilisateurs.
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.accounts.serializers import RegisterSerializer, UserSerializer


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
