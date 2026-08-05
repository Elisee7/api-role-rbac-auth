# Matrice Rôles -> Permissions (RBAC)

* **Ticket** : AUTH-005
* **Date** : 2026-08-05

## 1. Définition des Rôles

* **ADMIN** : Administrateur système disposant d'un accès total sur l'application et la gestion des utilisateurs/rôles.
* **MANAGER** : Gestionnaire métiers pouvant lire et modifier la majorité des ressources, mais ne pouvant pas gérer les rôles ni supprimer d'utilisateurs.
* **USER** : Utilisateur standard disposant des droits de lecture basiques et d'accès à son propre profil.

## 2. Tableau de la Matrice

| Permission (Code) | Description | ADMIN | MANAGER | USER |
| :--- | :--- | :---: | :---: | :---: |
| `users.read` | Consulter la liste/détails des utilisateurs | ✅ | ✅ | ❌ |
| `users.write` | Créer et modifier des utilisateurs | ✅ | ✅ | ❌ |
| `users.delete` | Supprimer des utilisateurs | ✅ | ❌ | ❌ |
| `roles.manage` | Créer, modifier et attribuer des rôles/permissions | ✅ | ❌ | ❌ |
| `profile.read` | Consulter son propre profil | ✅ | ✅ | ✅ |
| `profile.write` | Modifier son propre profil | ✅ | ✅ | ✅ |