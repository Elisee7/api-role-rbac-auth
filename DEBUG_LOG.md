# Journal des Erreurs et Débogage (Debug Log)

> Journal chronologique à numérotation continue.  
> Chaque entrée documente un problème rencontré, sa cause et sa résolution.

---

## 1. `ProgrammingError: relation "roles_role" does not exist`

- **Module concerné :** `apps.roles`
- **Cause :**
  Les tables de la base de données n’avaient pas été créées pour l’application `roles`.
  Cela pouvait venir de migrations manquantes ou de l’absence de l’application dans `INSTALLED_APPS`.
- **Résolution :**
  Vérifier la présence de `'apps.roles'` dans `INSTALLED_APPS` dans `settings.py`, puis exécuter :
  ```bash
  python manage.py makemigrations roles
  python manage.py migrate
  ```

---

## 2. `ImproperlyConfigured: Field name created_at is not valid for model Role`

- **Module concerné :** `apps.roles`
- **Cause :**
  Le champ `created_at` était déclaré dans le sérialiseur `RoleSerializer`, mais n’existait pas encore sur le modèle `Role`.
- **Résolution :**
  Ajouter le champ au modèle `Role` dans `apps/roles/models.py` :
  ```python
  created_at = models.DateTimeField(default=timezone.now)
  ```

---

## 3. `AttributeError: type object 'datetime.timezone' has no attribute 'now'`

- **Module concerné :** `apps.roles`
- **Cause :**
  Import incorrect du module `timezone` depuis la librairie standard Python :
  ```python
  from datetime import timezone
  ```
  Alors que Django fournit son propre utilitaire `timezone.now`.
- **Résolution :**
  Utiliser l’import Django dans `models.py` :
  ```python
  from django.utils import timezone
  ```

---

## 4. `TypeError: Permission() got unexpected keyword arguments: 'name'`

- **Module concerné :** `apps.roles`
- **Cause :**
  Le modèle `Permission` ne possède pas de champ `name`.
  Il utilise les champs `code` et `description`.
  Certains tests créaient cependant des permissions avec :
  ```python
  Permission.objects.create(name=...)
  ```
- **Résolution :**
  Remplacer `name` par les champs corrects dans `apps/roles/tests.py` :
  ```python
  Permission.objects.create(
      code="roles.manage",
      description="Manage Roles"
  )
  ```

---

## 5. `TypeError: UserManager.create_user() missing 1 required positional argument: 'username'`

- **Module concerné :** `apps.roles`
- **Cause :**
  La méthode `create_user()` du modèle utilisateur requiert l’argument obligatoire `username`.
  Cet argument n’était pas fourni lors du `setUp()` dans certains tests unitaires.
- **Résolution :**
  Spécifier systématiquement `username` lors des appels à :
  ```python
  User.objects.create_user(...)
  ```

---

## 6. `AssertionError: False is not true` — `test_user_with_required_permission_allowed`

- **Module concerné :** `apps.roles`
- **Cause :**
  L’utilisateur `self.user_with_perm` était créé sans rôle associé.
  Sa propriété `role` valait donc `None`, ce qui entraînait le refus de permission par `HasRolePermission`.
- **Résolution :**
  Associer le rôle lors de la création de l’utilisateur dans le `setUp()` :
  ```python
  User.objects.create_user(
      ...,
      role=self.role_admin
  )
  ```

---

## 7. [2026-08-10] `TypeError: UserManager.create_user() missing 1 required positional argument: 'username'` sur `UserMeTests`

- **Ticket associé :** `AUTH-023` — Profil utilisateur `/api/users/me/`
- **Symptômes :**
  L’exécution de `python manage.py test apps` renvoyait plusieurs erreurs sur `UserMeTests` :
  ```txt
  TypeError: UserManager.create_user() missing 1 required positional argument: 'username'
  ```
- **Cause :**
  Le modèle `CustomUser` définit :
  ```python
  REQUIRED_FIELDS = ['username']
  ```
  Lors de l’initialisation des utilisateurs de test dans `setUp()`, seul `email` était fourni, sans `username`.
- **Résolution :**
  Mettre à jour la création des utilisateurs dans `apps/accounts/tests.py` pour transmettre systématiquement :
  ```python
  username="testuser"
  ```

---

## 8. [2026-08-10] Restriction des méthodes HTTP sur `/api/users/me/`

- **Ticket associé :** `AUTH-023` — Profil utilisateur `/api/users/me/`
- **Symptômes / Recommandation :**
  Par défaut, `RetrieveUpdateAPIView` autorise notamment la méthode `PUT`.
  Conformément au cahier des charges, l’endpoint `/api/users/me/` ne doit exposer que `GET` et `PATCH`.
- **Résolution :**
  Ajustement de `UserMeView` dans `apps/accounts/views.py` :
  ```python
  class UserMeView(generics.RetrieveUpdateAPIView):
      http_method_names = ['get', 'patch', 'head', 'options']
  ```

---

## 9. [2026-08-11] Warnings de sécurité `check --deploy`

- **Ticket associé :** `AUTH-034` — Durcissement CORS / HTTPS
- **Symptômes :**
  L’exécution de :
  ```bash
  python manage.py check --deploy
  ```
  renvoyait plusieurs warnings de sécurité :
  ```txt
  ?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting...
  ?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True...
  ?: (security.W009) Your SECRET_KEY has less than 50 characters...
  ?: (security.W012) SESSION_COOKIE_SECURE is not set to True...
  ?: (security.W016) ...you have not set CSRF_COOKIE_SECURE to True...
  ?: (security.W018) You should not have DEBUG set to True in deployment.
  ```
- **Cause :**
  La configuration Django était encore orientée développement local :
  - `DEBUG=True`
  - `SECRET_KEY` non conforme pour la production
  - absence des paramètres HTTPS / HSTS
  - cookies de session et CSRF non sécurisés
- **Résolution :**
  Ajouter un bloc conditionnel dans `config/settings.py` afin d’activer les paramètres de sécurité uniquement lorsque `DEBUG=False` :
  ```python
  if not DEBUG:
      SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
      SESSION_COOKIE_SECURE = True
      CSRF_COOKIE_SECURE = True

      SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600"))
      SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
          "SECURE_HSTS_INCLUDE_SUBDOMAINS",
          default=True
      )
      SECURE_HSTS_PRELOAD = env_bool(
          "SECURE_HSTS_PRELOAD",
          default=False
      )

      if env_bool("SECURE_PROXY_SSL_HEADER", default=False):
          SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
  else:
      SECURE_SSL_REDIRECT = False
      SESSION_COOKIE_SECURE = False
      CSRF_COOKIE_SECURE = False
      SECURE_HSTS_SECONDS = 0
  ```

---

## 10. [2026-08-11] Tests API renvoyant `301` au lieu des codes attendus

- **Ticket associé :** `AUTH-034` — Durcissement CORS / HTTPS
- **Symptômes :**
  L’exécution de :
  ```bash
  python manage.py test
  ```
  renvoyait de nombreux échecs :
  ```txt
  AssertionError: 301 != 200
  AssertionError: 301 != 201
  AssertionError: 301 != 400
  AssertionError: 301 != 401
  AssertionError: 301 != 403
  AssertionError: 301 != 405
  AttributeError: 'HttpResponsePermanentRedirect' object has no attribute 'data'
  ```
- **Cause :**
  Des variables d’environnement de production avaient été chargées dans le shell courant avec :
  ```bash
  set -a
  source .env.production.local
  set +a
  ```
  Le fichier `.env.production.local` contenait notamment :
  ```env
  DEBUG=False
  SECURE_SSL_REDIRECT=True
  ```
  Les variables d’environnement du shell sont prioritaires sur `load_dotenv()`.
  Django utilisait donc `DEBUG=False`, ce qui activait `SECURE_SSL_REDIRECT=True`.
  Toutes les requêtes HTTP étaient alors redirigées vers HTTPS, renvoyant le code :
  ```txt
  301 Moved Permanently
  ```
- **Résolution :**
  Nettoyer l’environnement shell courant :
  ```bash
  unset DEBUG DJANGO_SECRET_KEY ALLOWED_HOSTS SECURE_SSL_REDIRECT
  unset SECURE_HSTS_SECONDS SECURE_HSTS_INCLUDE_SUBDOMAINS
  unset SECURE_HSTS_PRELOAD SECURE_PROXY_SSL_HEADER
  ```
  Puis relancer les tests :
  ```bash
  python manage.py test
  ```
  Résultat après nettoyage :
  ```txt
  Ran 27 tests
  OK
  ```

---

## 11. [2026-08-11] `InsecureKeyLengthWarning: The HMAC key is 9 bytes long`

- **Ticket associé :** `AUTH-034` — Durcissement CORS / HTTPS
- **Symptômes :**
  Pendant l’exécution des tests, le warning suivant apparaissait :
  ```txt
  jwt/api_jwt.py:147: InsecureKeyLengthWarning: The HMAC key is 9 bytes long,
  which is below the minimum recommended length of 32 bytes for SHA256.
  See RFC 7518 Section 3.2.
  ```
- **Cause :**
  La variable `DJANGO_SECRET_KEY` utilisée par Django provenait de l’environnement shell chargé depuis `.env.production.local`, avec une valeur placeholder trop courte :
  ```env
  DJANGO_SECRET_KEY=CHANGE_ME
  ```
  Cette valeur étant prioritaire sur le fichier `.env` local, SimpleJWT signait les tokens avec une clé trop faible.
- **Résolution :**
  Nettoyer la variable d’environnement shell :
  ```bash
  unset DJANGO_SECRET_KEY
  ```
  Générer une clé secrète forte :
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  Puis renseigner cette valeur dans le fichier `.env` local :
  ```env
  DJANGO_SECRET_KEY=CLE_SECRETE_GENEREE
  ```

---

## 12. [2026-08-11] Variables de production présentes dans le `.env` local

- **Ticket associé :** `AUTH-034` — Durcissement CORS / HTTPS
- **Symptômes :**
  Le fichier `.env` local contenait des variables destinées uniquement à la production :
  ```env
  DEBUG=True
  SECURE_SSL_REDIRECT=True
  SECURE_HSTS_SECONDS=3600
  SECURE_HSTS_INCLUDE_SUBDOMAINS=True
  SECURE_HSTS_PRELOAD=False
  ```
  Cela créait une configuration incohérente :
  - mode développement actif avec `DEBUG=True`
  - mais comportement sécurité production activé
- **Cause :**
  Les variables de durcissement HTTPS avaient été ajoutées directement dans le fichier `.env` de développement, au lieu d’être appliquées conditionnellement par `settings.py` ou isolées dans un fichier `.env.production.local`.
- **Résolution :**
  Retirer les variables `SECURE_*` du fichier `.env` local de développement.

  Les conserver uniquement dans :
  - `.env.example`, pour documentation
  - `.env.production.local`, ou variables d’environnement de déploiement, pour production

  Le bloc `if not DEBUG:` dans `settings.py` suffit à activer ces paramètres en production.

---

## 13. [2026-08-11] Imports et variables dupliqués dans `settings.py`

- **Module concerné :** `config/settings.py`
- **Symptômes :**
  Le fichier `settings.py` contenait des doublons :
  ```python
  from dotenv import load_dotenv
  load_dotenv()
  BASE_DIR = Path(__file__).resolve().parent.parent

  from dotenv import load_dotenv
  load_dotenv()
  BASE_DIR = Path(__file__).resolve().parent.parent
  ```
- **Cause :**
  Copié-collé successif de blocs de configuration sans nettoyage.
- **Résolution :**
  Supprimer les doublons et charger le fichier `.env` avec un chemin explicite :
  ```python
  from pathlib import Path
  from dotenv import load_dotenv

  BASE_DIR = Path(__file__).resolve().parent.parent
  load_dotenv(BASE_DIR / ".env")
  ```

---

## 14. [2026-08-11] Bonne pratique : tester la configuration production dans un subshell

- **Ticket associé :** `AUTH-034` — Durcissement CORS / HTTPS
- **Problème évité :**
  Charger `.env.production.local` dans le shell courant peut casser temporairement l’environnement de développement sans que l’on s’en rende compte immédiatement.
- **Pratique recommandée :**
  Tester la configuration production dans un subshell isolé :
  ```bash
  (
      set -a
      source .env.production.local
      set +a
      python manage.py check --deploy
  )
  ```
  À la fin du subshell, les variables sont automatiquement supprimées de l’environnement courant.

---

## 15. [2026-08-11] Validation finale après corrections

- **Commande exécutée :**
  ```bash
  python manage.py test
  ```
- **Résultat :**
  ```txt
  Ran 27 tests in 79.125s

  OK
  ```
- **Conclusion :**
  Les 27 tests passent après nettoyage de l’environnement shell et sécurisation de la configuration.