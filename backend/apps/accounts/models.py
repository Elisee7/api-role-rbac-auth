"""
Fichier : apps/accounts/models.py
Description : Modèle Utilisateur personnalisé (CustomUser).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Modèle utilisateur personnalisé.
    Utilise l'email comme identifiant principal et prévoie la relation vers Role.
    """
    email = models.EmailField(unique=True, verbose_name="Adresse email")

    # Relation vers le rôle (sera activée après création du modèle Role)
    role = models.ForeignKey(
        'roles.Role',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name="Rôle applicatif"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'auth_user_custom'
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'

    def __str__(self):
        return f"{self.email} ({self.role.name if self.role else 'Sans rôle'})"