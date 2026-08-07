from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.roles.models import Role
import jwt
from django.conf import settings

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

class LoginAPITestCase(APITestCase):
    """
    Test 2 du Cahier des Charges : Connexion et émission des tokens JWT.
    """
    def setUp(self):
        self.user_role = Role.objects.create(name='USER', description='Utilisateur standard')
        self.email = "loginuser@example.com"
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(
            email=self.email,
            username="loginuser",
            password=self.password,
            role=self.user_role
        )
        self.login_url = reverse('auth-login')

    def test_login_success(self):
        """
        Vérifie que la connexion avec identifiants valides retourne un access token et un refresh token.
        """
        data = {
            "email": self.email,
            "password": self.password
        }
        response = self.client.post(self.login_url, data, format='json')

        # Assertions HTTP & Tokens
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], self.email)

        # Vérification du contenu du token (Claims)
        access_token = response.data['access']
        decoded_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=["HS256"], options={"verify_signature": False})
        self.assertEqual(decoded_payload['role'], 'USER')
        self.assertEqual(decoded_payload['email'], self.email)

    def test_login_invalid_credentials(self):
        """
        Vérifie le rejet d'une connexion avec un mauvais mot de passe.
        """
        data = {
            "email": self.email,
            "password": "WrongPassword123!"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
