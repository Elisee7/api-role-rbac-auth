"""
Fichier : apps/accounts/serializers.py
Description : Sérialiseurs pour la gestion des utilisateurs et de l'authentification.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from apps.roles.models import Role
from apps.roles.serializers import RoleSerializer
from django.core.exceptions import ValidationError as DjangoValidationError


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
        """
        Validation globale du sérialiseur.
        Instancie un utilisateur candidat en mémoire pour permettre
        à UserAttributeSimilarityValidator de comparer le mot de passe
        aux attributs (email, username, etc.).
        Les erreurs sont associées au champ 'password' pour une réponse
        API structurée par champ (meilleure intégration frontend).
        """
        candidate_user = User(
            email=attrs.get('email', ''),
            username=attrs.get('username', ''),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            validate_password(attrs['password'], candidate_user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': exc.messages})
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

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Sérialiseur de connexion JWT (AUTH-011 & AUTH-014).
    Authentifie l'utilisateur via son email et injecte le rôle dans le payload du token.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # AUTH-014 : Custom claims dans le JWT
        token['email'] = user.email
        token['username'] = user.username
        token['role'] = user.role.name if user.role else None

        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Enrichissement du corps de la réponse JSON au login
        data['user'] = UserSerializer(self.user).data
        return data

class LogoutSerializer(serializers.Serializer):
    """
    Sérialiseur pour valider le refresh token fourni lors de la déconnexion.
    Effectue la mise en liste noire (blacklist) du token lors de l'exécution de save().
    """
    refresh = serializers.CharField(
        help_text="Le token de rafraîchissement à invalider."
    )

    def validate(self, attrs):
        """
        Vérification de la présence et du format du token.
        """
        self.token = attrs.get('refresh')
        return attrs

    def save(self, **kwargs):
        """
        Invalide le refresh token en l'ajoutant à la liste noire (Blacklist).
        Lève une TokenError si le token est expiré ou invalide.
        """
        try:
            token = RefreshToken(self.token)
            token.blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {'refresh': 'Token invalide ou déjà révoqué.'}
            )

class UserAssignRoleSerializer(serializers.Serializer):
    """
    Sérialiseur de validation pour l'assignation d'un rôle à un utilisateur.
    """
    role_id = serializers.IntegerField(required=True, help_text="ID du rôle à attribuer")

    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError("Le rôle spécifié n'existe pas.")
        return value


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Sérialiseur détaillé pour afficher les informations de l'utilisateur avec son rôle.
    """
    role = RoleSerializer(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'username','first_name', 'last_name', 'role', 'is_active', 'date_joined')
        read_only_fields = fields


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur permettant à un utilisateur de mettre à jour son propre profil.
    Les champs sensibles (email, role, is_staff, etc.) sont exclus du champ d'édition.
    """
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username')

    def validate_username(self, value):
        """
        Vérifie l'unicité du nom d'utilisateur si celui-ci est modifié.
        """
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return value