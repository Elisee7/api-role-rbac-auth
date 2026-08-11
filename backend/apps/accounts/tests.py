from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.roles.models import Role, Permission
from rest_framework_simplejwt.state import token_backend
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken
from django.core.cache import cache
from unittest import mock
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from datetime import timedelta

User = get_user_model()


class RegisterAPITestCase(APITestCase):
    """
    Test 1 du Cahier des Charges : Verification de l'inscription d'un utilisateur.
    """
    def setUp(self):
        super().setUp()
        cache.clear()
        # Pré-création du rôle USER pour l'attribution automatique
        self.user_role = Role.objects.create(name='USER', description='Utilisateur standard')
        self.register_url = reverse('auth-register')

    def tearDown(self):
        cache.clear()
        super().tearDown()

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
        super().setUp()
        cache.clear()
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

    def tearDown(self):
        cache.clear()
        super().tearDown()

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
        super().setUp()
        cache.clear()
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

        def tearDown(self):
            cache.clear()
            super().tearDown()

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
        super().setUp()
        cache.clear()
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

        def tearDown(self):
            cache.clear()
            super().tearDown()

    def test_logout_success(self):
        """
        Vérifie qu'un utilisateur authentifié peut révoquer son refresh token.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        response = self.client.post(self.logout_url, {'refresh': self.refresh_token})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

class UserAssignRoleTestCase(APITestCase):
    def setUp(self):
        # Permissions & Rôles
        self.perm_manage = Permission.objects.create(code='roles.manage', description='Gérer les rôles')
        
        self.admin_role = Role.objects.create(name='ADMIN')
        self.admin_role.permissions.add(self.perm_manage)
        
        self.user_role = Role.objects.create(name='USER')
        self.manager_role = Role.objects.create(name='MANAGER')

        # Utilisateurs
        self.admin_user = User.objects.create_user(
            email="admin@example.com", username="adminuser", password="Password123!", role=self.admin_role
        )
        self.standard_user = User.objects.create_user(
            email="user@example.com", username="standarduser", password="Password123!", role=self.user_role
        )
        self.target_user = User.objects.create_user(
            email="target@example.com", username="targetuser", password="Password123!", role=self.user_role
        )

    def test_admin_can_assign_role(self):
        """Un administrateur peut assigner un nouveau rôle à un utilisateur."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-assign-role', kwargs={'pk': self.target_user.pk})
        response = self.client.post(url, {'role_id': self.manager_role.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.role, self.manager_role)

    def test_standard_user_cannot_assign_role(self):
        """Un utilisateur standard ne peut pas assigner de rôle (403 Forbidden)."""
        self.client.force_authenticate(user=self.standard_user)
        url = reverse('user-assign-role', kwargs={'pk': self.target_user.pk})
        response = self.client.post(url, {'role_id': self.manager_role.id})
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_invalid_role_returns_400(self):
        """Tenter d'assigner un role_id inexistant renvoie un 400 Bad Request."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('user-assign-role', kwargs={'pk': self.target_user.pk})
        response = self.client.post(url, {'role_id': 9999})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class UserMeTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="Password123!",
            first_name="John",
            last_name="Doe"
        )
        self.url = reverse('user-me')

    def test_get_user_me_authenticated(self):
        """Vérifie la récupération du profil pour un utilisateur connecté."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['first_name'], "John")

    def test_get_user_me_unauthenticated(self):
        """Vérifie qu'un accès non authentifié retourne 401 Unauthorized."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_user_me_success(self):
        """Vérifie la mise à jour partielle des champs autorisés (first_name, last_name)."""
        self.client.force_authenticate(user=self.user)
        payload = {"first_name": "Jane", "last_name": "Smith"}
        response = self.client.patch(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Jane")
        self.assertEqual(self.user.last_name, "Smith")

    def test_patch_user_me_cannot_change_readonly_fields(self):
        """Vérifie qu'un utilisateur ne peut pas modifier son email ou son rôle via ce flux."""
        self.client.force_authenticate(user=self.user)
        payload = {"email": "hacked@example.com"}
        response = self.client.patch(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        # L'email ne doit pas avoir changé
        self.assertEqual(self.user.email, "testuser@example.com")

    def test_put_user_me_not_allowed(self):
        """Vérifie que la méthode PUT est rejetée avec un statut 405 Method Not Allowed."""
        self.client.force_authenticate(user=self.user)
        payload = {"first_name": "Jane", "last_name": "Smith"}
        response = self.client.put(self.url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_head_user_me_success(self):
        """Vérifie que la méthode HEAD retourne un 200 OK avec des en-têtes mais sans body."""
        self.client.force_authenticate(user=self.user)
        response = self.client.head(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.content, b'')  # Le corps de la réponse doit être vide

# ---------------------------------------------------------------------------
# AUTH-033 : tests de rate limiting sur les endpoints sensibles.
#
# Objectif :
# - vérifier que /api/auth/login/ renvoie 429 après dépassement de la limite ;
# - vérifier que /api/auth/refresh/ renvoie 429 après dépassement de la limite.
#
# Important :
# `override_settings(REST_FRAMEWORK=...)` n'est pas suffisant ici, car DRF
# charge les limites de throttling dans l'attribut de classe
# `SimpleRateThrottle.THROTTLE_RATES` au moment de l'import du module.
# On patch donc directement la classe `ScopedRateThrottle` utilisée par les vues.
# ---------------------------------------------------------------------------

# Nombre maximal de requêtes autorisées pendant la fenêtre de test.
TEST_AUTH_RATE_LIMIT = 3

# Valeur de rate limiting utilisée uniquement pour les tests.
TEST_AUTH_RATE = f"{TEST_AUTH_RATE_LIMIT}/minute"


@mock.patch.object(
    ScopedRateThrottle,
    "THROTTLE_RATES",
    {"auth": TEST_AUTH_RATE},
)
class AuthRateLimitingTestCase(APITestCase):
    """
    Suite de tests pour AUTH-033.

    Vérifie que les endpoints d'authentification sensibles renvoient :
    - 401 tant que la limite de débit n'est pas dépassée ;
    - 429 lorsque la limite de débit est dépassée.

    Les endpoints testés sont :
    - POST /api/auth/login/
    - POST /api/auth/refresh/
    """

    def setUp(self):
        """
        Nettoie le cache avant chaque test.

        DRF utilise le cache pour stocker les compteurs de throttling.
        Ce nettoyage évite qu'un test précédent ne fausse le résultat.
        """
        super().setUp()
        cache.clear()

    def tearDown(self):
        """
        Nettoie le cache après chaque test afin de ne pas polluer
        les tests suivants avec des compteurs de throttling résiduels.
        """
        cache.clear()
        super().tearDown()

    def test_login_rate_limit_returns_429(self):
        """
        Vérifie que /api/auth/login/ est protégé contre le brute force.

        Scénario :
        1. On envoie plusieurs tentatives de connexion invalides.
        2. Tant que la limite n'est pas atteinte, l'API répond 401.
        3. Une fois la limite dépassée, l'API répond 429.
        """
        url = reverse('auth-login')

        payload = {
            "email": "unknown@example.com",
            "password": "WrongPassword123!",
        }

        # Les premières requêtes doivent être refusées pour identifiants invalides.
        for _ in range(TEST_AUTH_RATE_LIMIT):
            response = self.client.post(url, payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # La requête suivante doit être bloquée par le rate limiting.
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_refresh_rate_limit_returns_429(self):
        """
        Vérifie que /api/auth/refresh/ est protégé contre l'abus de requêtes.

        Scénario :
        1. On envoie plusieurs refresh tokens invalides.
        2. Tant que la limite n'est pas atteinte, l'API répond 401.
        3. Une fois la limite dépassée, l'API répond 429.
        """
        url = reverse('auth-refresh')

        payload = {
            "refresh": "invalid.token.string",
        }

        # Les premières requêtes doivent être refusées pour token invalide.
        for _ in range(TEST_AUTH_RATE_LIMIT):
            response = self.client.post(url, payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # La requête suivante doit être bloquée par le rate limiting.
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

class RegisterValidationTestCase(APITestCase):
    """
    Tests complémentaires (CDC §10) sur la validation à l'inscription :
    - rejet d'un mot de passe faible ;
    - rejet d'un email déjà existant.
    """

    def setUp(self):
        """Pré-création du rôle USER requis par RegisterSerializer."""
        Role.objects.create(name='USER', description='Utilisateur standard')
        self.register_url = reverse('auth-register')

    def test_register_weak_password_rejected(self):
        """
        Vérifie qu'un mot de passe trop faible (ex: '123') est rejeté
        avec un statut 400 et un message d'erreur explicite.
        """
        data = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "123",
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # validate_password() est appelé dans validate() global du sérialiseur,
        # les erreurs sont donc dans non_field_errors.
        self.assertIn('password', response.data)

    def test_register_duplicate_email_rejected(self):
        """
        Vérifie qu'une inscription avec un email déjà existant
        est rejetée avec un statut 400.
        """
        # Premier utilisateur
        User.objects.create_user(
            email="existing@example.com",
            username="existinguser",
            password="StrongPassword123!",
        )
        # Tentative de doublon
        data = {
            "email": "existing@example.com",
            "username": "anotheruser",
            "password": "StrongPassword123!",
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class AccessTokenExpiryTestCase(APITestCase):
    """
    Test complémentaire (CDC §10) : expiration de l'access token.
    Vérifie qu'un access token expiré est rejeté avec un statut 401.
    """

    def setUp(self):
        """Création d'un utilisateur pour générer un token expiré."""
        self.user = User.objects.create_user(
            username="expiryuser",
            email="expiry@example.com",
            password="StrongPassword123!",
        )
        self.url = reverse('user-me')

    def test_expired_access_token_rejected(self):
        """
        Génère un access token avec une durée de vie négative
        (déjà expiré) et vérifie que l'API répond 401.
        """
        token = AccessToken.for_user(self.user)
        token.set_exp(lifetime=timedelta(minutes=-1))
        expired_access = str(token)

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {expired_access}'
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)