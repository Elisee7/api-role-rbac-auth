# Journal des Erreurs et Débogage (Debug Log)

### 1. `ProgrammingError: relation "roles_role" does not exist`
* **Cause :** Les tables de la base de données n'ont pas été créées pour l'application `roles` (migrations manquantes ou application non enregistrée dans `INSTALLED_APPS`).
* **Résolution :** Vérifier la présence de `'apps.roles'` dans `INSTALLED_APPS` dans `settings.py`, puis exécuter `python manage.py makemigrations roles` et `python manage.py migrate`.

---

### 2. `ImproperlyConfigured: Field name created_at is not valid for model Role`
* **Cause :** Le champ `created_at` était déclaré dans le sérialiseur (`RoleSerializer`), mais n'existait pas sur le modèle `Role`.
* **Résolution :** Ajouter le champ `created_at = models.DateTimeField(default=timezone.now)` au modèle `Role` dans `apps/roles/models.py`.

---

### 3. `AttributeError: type object 'datetime.timezone' has no attribute 'now'`
* **Cause :** Import incorrect du module `timezone` depuis la librairie standard Python (`from datetime import timezone`) au lieu de celui de Django.
* **Résolution :** Utiliser l'importateur spécifique à Django dans `models.py` (`from django.utils import timezone`).

---

### 4. `TypeError: Permission() got unexpected keyword arguments: 'name'`
* **Cause :** Le modèle `Permission` ne possède pas de champ `name` (il utilise `code` et `description`), mais le fichier de test instanciait des objets avec `Permission.objects.create(name=...)`.
* **Résolution :** Remplacer `name` par `description` ou le supprimer lors de la création d'objets dans `apps/roles/tests.py` (`Permission.objects.create(code="roles.manage", description="Manage Roles")`).

---

### 5. `TypeError: UserManager.create_user() missing 1 required positional argument: 'username'`
* **Cause :** La méthode `create_user()` du modèle utilisateur requiert l'argument obligatoire `username`, qui n'était pas fourni lors du `setUp()` dans les tests unitaires.
* **Résolution :** Spécifier l'argument `username` lors de chaque appel à `User.objects.create_user()` dans `apps/roles/tests.py`.

---

### 6. `AssertionError: False is not true` (`test_user_with_required_permission_allowed`)
* **Cause :** L'utilisateur `self.user_with_perm` était instancié sans lui associer le rôle `self.role_admin`. Sa propriété `role` valait `None`, entraînant le refus de permission par `HasRolePermission`.
* **Résolution :** Associer le rôle lors de la création de l'utilisateur dans le `setUp()` (`User.objects.create_user(..., role=self.role_admin)`).

## [2026-08-10] Fix: TypeError create_user() et Restriction HTTP 405 sur AUTH-023

**Ticket associé :** `AUTH-023` (Profil utilisateur `/api/users/me/`)

### 1. Problème : Argument `username` manquant dans les tests unitaires
* **Symptômes :** 
  L'exécution de `python manage.py test apps` renvoyait 4 erreurs sur `UserMeTests` :
  `TypeError: UserManager.create_user() missing 1 required positional argument: 'username'`
* **Cause :** 
  Le modèle `CustomUser` définit `REQUIRED_FIELDS = ['username']`. Lors de l'initialisation de l'utilisateur de test dans `setUp()`, seul `email` était fourni sans l'argument `username`.
* **Solution :** 
  Mise à jour du helper `create_user` dans `apps/accounts/tests.py` pour transmettre le champ `username="testuser"`.

### 2. Correction Revue Code : Restriction des méthodes HTTP (CodeRabbit)
* **Symptômes / Recommandation :** 
  Par défaut, `RetrieveUpdateAPIView` autorise la méthode `PUT`. Conformément au CDC et au ticket AUTH-023, l'endpoint ne doit exposer que `GET` et `PATCH`.
* **Solution :** 
  Ajustement de `UserMeView` dans `apps/accounts/views.py` :
  ```python
  class UserMeView(generics.RetrieveUpdateAPIView):
      http_method_names = ['get', 'patch', 'head', 'options']