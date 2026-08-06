from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.roles.models import Role

User = get_user_model()


class RegisterAPITestCase(APITestCase):
    """
    Test 1 du Cahier des Charges : Verification de l'inscription d'un utilisateur.
    """
    def setUp(self):
        # Pré-création du rôle USER pour l'attribution automatique
        self.user_role = Role.objects.create(name='USER', description='Utilisateur standard')
        self.register_url = reverse('auth-register')

    def test_user_registration_success(self):
        """
        Vérifie qu'un utilisateur peut créer un compte avec des données valides.
        Résultat attendu : statut 201, mot de passe haché (jamais en clair).
        """
        data = {
            "email": "testuser@example.com",
            "username": "testuser",
            "password": "StrongPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }
        response = self.client.post(self.register_url, data, format='json')

        # Assertions HTTP
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], data['email'])
        self.assertEqual(response.data['role'], 'USER')
        self.assertNotIn('password', response.data)

        # Assertions Base de données
        user = User.objects.get(email=data['email'])
        self.assertTrue(user.check_password(data['password']))  # Vérifie que le mot de passe est haché
        self.assertNotEqual(user.password, data['password'])  # Jamais en clair
