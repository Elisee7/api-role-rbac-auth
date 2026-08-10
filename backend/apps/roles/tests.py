from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from apps.roles.models import Role, Permission

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