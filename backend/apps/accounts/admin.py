from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from apps.accounts.models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Rôle applicatif', {'fields': ('role',)}),
    )
    list_display = ('email', 'username', 'role', 'is_active', 'is_staff')