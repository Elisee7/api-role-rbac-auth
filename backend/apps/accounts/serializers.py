"""
Fichier : apps/accounts/serializers.py
Description : Sérialiseurs pour la gestion des utilisateurs et de l'authentification.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from apps.roles.models import Role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la lecture des informations d'un utilisateur.
    Expose le nom du rôle pour éviter de renvoyer un simple ID.
    """
    role = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'role', 'date_joined')
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création de compte (AUTH-010).
    Valide les données, applique les règles de sécurité sur le mot de passe,
    hache le mot de passe et attribue le rôle par défaut 'USER'.
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        help_text="Mot de passe conforme aux exigences de sécurité Django."
    )

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'password')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

    def validate(self, attrs):
        # Instanciation d'un utilisateur candidat en mémoire pour valider la similitude d'attributs
        candidate_user = User(
            email=attrs.get('email', ''),
            username=attrs.get('username', ''),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        validate_password(attrs['password'], candidate_user)
        return attrs

    def create(self, validated_data):
        # Récupération du rôle par défaut 'USER' (s'il existe en BDD)
        default_role = Role.objects.filter(name='USER').first()
        if default_role is None:
            raise serializers.ValidationError(
                {'non_field_errors': ['Default USER role is not configured.']}
            )
        
        # Création sécurisée de l'utilisateur avec hachage automatique du mot de passe
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=default_role
        )
        return user

