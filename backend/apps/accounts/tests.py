from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.roles.models import Role
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.tokens import RefreshToken

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

        # Vérification sécurisée du contenu du token (Claims + Signature)
        access_token = response.data['access']
        decoded_payload = token_backend.decode(access_token)
        
        self.assertEqual(decoded_payload['role'], 'USER')
        self.assertEqual(decoded_payload['email'], self.email)
        self.assertEqual(decoded_payload['username'], self.user.username)

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

class TokenRefreshAPITestCase(APITestCase):
    """
    Test 3 du Cahier des Charges : Rafraîchissement du token JWT et rotation.
    """
    def setUp(self):
        self.user_role = Role.objects.create(name='USER', description='Utilisateur standard')
        self.email = "refreshuser@example.com"
        self.password = "StrongPassword123!"
        self.user = User.objects.create_user(
            email=self.email,
            username="refreshuser",
            password=self.password,
            role=self.user_role
        )
        self.login_url = reverse('auth-login')
        self.refresh_url = reverse('auth-refresh')

        # Connexion initiale pour obtenir les tokens
        response = self.client.post(self.login_url, {
            "email": self.email,
            "password": self.password
        }, format='json')
        self.initial_refresh = response.data['refresh']
        self.initial_access = response.data['access']

    def test_token_refresh_success_and_rotation(self):
        """
        1. Vérifie le rafraîchissement réussi de l'access token.
        2. Vérifie que la rotation génère un tout nouveau refresh token.
        3. Vérifie que l'ancien refresh token est désormais invalidé (blacklisté).
        """
        # Étape 1 : Demande de rafraîchissement avec le token initial
        response = self.client.post(self.refresh_url, {
            "refresh": self.initial_refresh
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        new_refresh = response.data['refresh']
        self.assertNotEqual(self.initial_refresh, new_refresh)  # Rotation effectuée

        # Étape 2 : Tentative de réutilisation de l'ancien refresh token (Doit échouer)
        failed_response = self.client.post(self.refresh_url, {
            "refresh": self.initial_refresh
        }, format='json')

        self.assertEqual(failed_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_invalid_token(self):
        """
        Vérifie qu'un token invalide ou corrompu est rejeté avec un statut 401.
        """
        response = self.client.post(self.refresh_url, {
            "refresh": "invalid.token.string"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class LogoutTests(APITestCase):
    """
    Suite de tests unitaires pour le ticket AUTH-013 (Déconnexion / Blacklist).
    """

    def setUp(self):
        """
        Initialisation de l'utilisateur de test et génération directe des tokens JWT.
        """
        self.user_data = {
            'username': 'logoutuser',
            'email': 'logoutuser@example.com',
            'password': 'StrongPassword123!'
        }
        self.user = User.objects.create_user(**self.user_data)

        # Génération directe et fiable des tokens via SimpleJWT (sans repasser par l'API de login)
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        self.logout_url = reverse('auth-logout')

    def test_logout_success(self):
        """
        Vérifie qu'un utilisateur authentifié peut révoquer son refresh token.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.logout_url, {'refresh': self.refresh_token})

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # Vérification : Le refresh token révoqué ne doit plus permettre de rafraîchir la session
        refresh_url = reverse('auth-refresh')
        refresh_response = self.client.post(refresh_url, {'refresh': self.refresh_token})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_unauthenticated(self):
        """
        Vérifie qu'une requête sans Access Token dans le header est rejetée (401 Unauthorized).
        """
        # On s'assure qu'aucun header d'autorisation n'est présent
        self.client.credentials()
        response = self.client.post(self.logout_url, {'refresh': self.refresh_token})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_invalid_refresh_token(self):
        """
        Vérifie qu'un refresh token invalide renvoie une erreur 400 Bad Request.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.logout_url, {'refresh': 'token_invalid_exemple'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

