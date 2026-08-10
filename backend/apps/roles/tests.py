from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.roles.models import Role, Permission
from apps.roles.permissions import HasRolePermission
from rest_framework.test import APIRequestFactory

User = get_user_model()

class RoleCRUDAPITestCase(APITestCase):
    def setUp(self):
        # Création de la permission et des rôles
        self.perm_manage = Permission.objects.create(code='roles.manage', description='Gérer les rôles')
        self.admin_role = Role.objects.create(name='ADMIN')
        self.admin_role.permissions.add(self.perm_manage)
        
        self.user_role = Role.objects.create(name='USER')

        # Utilisateur Admin
        self.admin_user = User.objects.create_user(
            email="admin@example.com", username="adminuser", password="Password123!", role=self.admin_role
        )
        # Utilisateur Standard
        self.standard_user = User.objects.create_user(
            email="user@example.com", username="standarduser", password="Password123!", role=self.user_role
        )
        
        self.roles_url = reverse('role-list')

    def test_admin_can_list_roles(self):
        """Un administrateur avec 'roles.manage' peut consulter les rôles."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.roles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_standard_user_cannot_list_roles(self):
        """Un utilisateur sans la permission 'roles.manage' reçoit un 403 Forbidden."""
        self.client.force_authenticate(user=self.standard_user)
        response = self.client.get(self.roles_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class HasRolePermissionUnitTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.permission_check = HasRolePermission()

        # Création des permissions et rôles
        self.perm = Permission.objects.create(code="roles.manage", description="Manage Roles")
        self.role_admin = Role.objects.create(name="Manager")
        self.role_admin.permissions.add(self.perm)

        self.role_user = Role.objects.create(name="User")

        # Création des utilisateurs
        self.user_with_perm = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            role=self.role_admin
        )
        self.user_without_perm = User.objects.create_user(
            username="userwithoutperm",
            email="user@test.com",
            password="password123",
            role=self.role_user
        )
        self.user_no_role = User.objects.create_user(
            username="norole",
            email="norole@test.com",
            password="password123"
        )
        self.superuser = User.objects.create_superuser(
            username="admin",
            email="admin@test.com",
            password="password123"
        )

        # Mock View
        class DummyView:
            required_permission = "roles.manage"

        self.view = DummyView()

    def test_anonymous_user_denied(self):
        request = self.factory.get("/")
        request.user = None
        self.assertFalse(self.permission_check.has_permission(request, self.view))

    def test_superuser_always_allowed(self):
        request = self.factory.get("/")
        request.user = self.superuser
        self.assertTrue(self.permission_check.has_permission(request, self.view))

    def test_user_without_role_denied(self):
        request = self.factory.get("/")
        request.user = self.user_no_role
        self.assertFalse(self.permission_check.has_permission(request, self.view))

    def test_user_without_required_permission_denied(self):
        request = self.factory.get("/")
        request.user = self.user_without_perm
        self.assertFalse(self.permission_check.has_permission(request, self.view))

    def test_user_with_required_permission_allowed(self):
        request = self.factory.get("/")
        request.user = self.user_with_perm
        self.assertTrue(self.permission_check.has_permission(request, self.view))