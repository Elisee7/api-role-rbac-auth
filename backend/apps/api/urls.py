"""
Fichier : apps/api/urls.py
Description : Centralisation du routage de l'API REST.
"""
from django.urls import path, include

urlpatterns = [
    path('', include('apps.accounts.urls')),
]