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

- **Module concerné :** `apps.roles`, `apps.accounts`
- **Cause :**
  Les tests appelaient :
  ```python
  User.objects.create_user(
      email=...,
      password=...
  )
  ```
  sans fournir `username`.

  Le manager par défaut hérité de Django impose `username` comme argument obligatoire :
  ```python
  def create_user(self, username, email=None, password=None, **extra_fields):
      ...
  ```

  `REQUIRED_FIELDS` n’est pas la cause directe de cette erreur.
  `REQUIRED_FIELDS` est utilisé par la commande `createsuperuser`, pas par la signature de `UserManager.create_user()`.
- **Diagnostic :**
  ```bash
  rg -n "REQUIRED_FIELDS|def create_user" .
  ```
- **Résolution :**
  Fournir systématiquement `username` dans les appels de test :
  ```python
  User.objects.create_user(
      username="testuser",
      email="test@example.com",
      password="StrongPassword123!"
  )
  ```

  À terme, si la création d’utilisateur doit se faire uniquement par email, il faudra implémenter un manager personnalisé avec une signature adaptée.

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
  Les utilisateurs de test étaient créés avec `email` et `password`, mais sans `username`.

  La cause réelle vient de la signature du manager utilisateur hérité de Django :
  ```python
  def create_user(self, username, email=None, password=None, **extra_fields):
      ...
  ```

  `REQUIRED_FIELDS` n’ajoute pas un argument obligatoire à `UserManager.create_user()`.
  Il est seulement utilisé par `createsuperuser`.
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

## 9. [2026-08-10] Warnings de sécurité `check --deploy`

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
  La commande `check --deploy` vérifie une posture de production.
  Elle a été exécutée avec une configuration de développement :
  - `DEBUG=True`
  - `SECRET_KEY` non conforme pour la production
  - absence de configuration HTTPS/HSTS effective
  - cookies de session et CSRF non sécurisés

  Le code de configuration n’active le durcissement production que lorsque `DEBUG=False`.
  Lorsque `DEBUG=True`, la branche `else` désactive explicitement :
  - `SECURE_SSL_REDIRECT`
  - `SESSION_COOKIE_SECURE`
  - `CSRF_COOKIE_SECURE`
  - `SECURE_HSTS_SECONDS`

  Les warnings étaient donc attendus en développement.
  Le problème était de vouloir valider une configuration de production avec un environnement de développement.
- **Résolution :**
  Valider la configuration de production dans un environnement dédié, avec :
  - `DEBUG=False`
  - une clé secrète forte
  - des variables `SECURE_*` correctement définies
  - un fichier `.env.production.local` ou un gestionnaire de secrets à jour

  Dans `config/settings.py`, conserver un bloc conditionnel clair :
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
  Django utilisait donc `DEBUG=False`, ce qui activait la branche production :
  ```python
  if not DEBUG:
      SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)
  ```

  Toutes les requêtes HTTP étaient alors redirigées vers HTTPS, renvoyant le code :
  ```txt
  301 Moved Permanently
  ```

  Avec `DEBUG=True`, la branche `else` du fichier `settings.py` force au contraire :
  ```python
  SECURE_SSL_REDIRECT = False
  SECURE_HSTS_SECONDS = 0
  ```

  Le problème ne venait donc pas de `DEBUG=True`, mais du fait que `DEBUG=False` avait été injecté accidentellement dans le shell courant.
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
  Pour corriger l’environnement shell courant :
  ```bash
  unset DJANGO_SECRET_KEY
  ```

  Générer une clé secrète forte :
  ```bash
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```

  Ensuite :
  1. renseigner cette valeur dans le fichier `.env` local pour le développement ;
  2. remplacer impérativement le placeholder dans `.env.production.local` ou dans le gestionnaire de secrets de déploiement ;
  3. ne pas considérer la mise à jour du `.env` local comme une correction de production.

  Si `.env.production.local` a déjà été partagé ou versionné avec un placeholder ou une vraie clé, la valeur doit être considérée comme compromise et remplacée.

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

  Cela créait une configuration confuse :
  - mode développement actif avec `DEBUG=True`
  - mais variables de sécurité production présentes dans le fichier de développement
- **Cause :**
  Les variables `SECURE_*` avaient été ajoutées dans le fichier `.env` local, alors qu’elles ne sont utiles que pour la validation ou l’exécution en production.

  Avec le code actuel de `settings.py`, lorsque `DEBUG=True`, la branche `else` force explicitement :
  ```python
  SECURE_SSL_REDIRECT = False
  SESSION_COOKIE_SECURE = False
  CSRF_COOKIE_SECURE = False
  SECURE_HSTS_SECONDS = 0
  ```

  Ces variables `SECURE_*` présentes dans le `.env` local n’activaient donc pas réellement le comportement production tant que `DEBUG=True` restait effectif.

  Le risque principal était :
  - la confusion dans la lecture de la configuration ;
  - un basculement accidentel vers `DEBUG=False` via l’environnement shell ;
  - une future lecture non conditionnelle de ces variables dans `settings.py`.
- **Résolution :**
  Retirer les variables `SECURE_*` du fichier `.env` local de développement.

  Les conserver uniquement dans :
  - `.env.example`, pour documentation ;
  - `.env.production.local`, ou variables d’environnement de déploiement, pour production.

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

## 14. [2026-08-11] Bonne pratique : tester la configuration production dans un subshell fail closed

- **Ticket associé :** `AUTH-034` — Durcissement CORS / HTTPS
- **Problème évité :**
  Charger `.env.production.local` dans le shell courant peut casser temporairement l’environnement de développement.

  De plus, une commande naïve comme :
  ```bash
  (
      set -a
      source .env.production.local
      set +a
      python manage.py check --deploy --fail-level WARNING
  )
  ```
  peut valider une configuration mixte ou involontaire si :
  - le fichier `.env.production.local` est absent ou illisible ;
  - `source` échoue mais la commande continue ;
  - des variables héritées du shell courant ne sont pas nettoyées avant chargement.
- **Pratique recommandée :**
  Tester la configuration production dans un subshell isolé et fail closed :
  ```bash
  (
      set -e

      # Vérifier que le fichier de configuration production est lisible.
      test -r .env.production.local

      (
    set -euo pipefail

    ENV_FILE=".env.production.local"

    # Vérifier que le fichier de configuration production est lisible.
    test -r "$ENV_FILE"

    # Nettoyer les variables héritées qui pourraient fausser la validation.
    unset DEBUG DJANGO_SECRET_KEY ALLOWED_HOSTS SECURE_SSL_REDIRECT
    unset SECURE_HSTS_SECONDS SECURE_HSTS_INCLUDE_SUBDOMAINS
    unset SECURE_HSTS_PRELOAD SECURE_PROXY_SSL_HEADER

    # Indiquer explicitement à settings.py de ne PAS charger le .env local

    # Charger les variables du fichier production.
    set -a
    . "$ENV_FILE"
    set +a
    export DJANGO_ENV="production"

    # Valider la valeur effectivement parsée et exposée à Django.
    python - <<'PY'
import os
import sys

secret = os.getenv("DJANGO_SECRET_KEY", "")

# Nettoyage des espaces et d'éventuels guillemets résiduels.
secret = secret.strip().strip("'\"")

if not secret:
    sys.exit("Erreur : DJANGO_SECRET_KEY est absente.")

normalized = secret.upper()

if (
    "CHANGE_ME" in normalized
    or "CHANGEME" in normalized
    or "PLACEHOLDER" in normalized
):
    sys.exit(
        "Erreur : DJANGO_SECRET_KEY contient encore un placeholder "
        "dans .env.production.local."
    )

if len(secret) < 50:
    sys.exit(
        "Erreur : DJANGO_SECRET_KEY doit contenir au moins 50 caractères."
    )

if len(set(secret)) < 5:
    sys.exit(
        "Erreur : DJANGO_SECRET_KEY manque d'entropie."
    )
PY

    python manage.py check --deploy
  )
  )
  ```

  Ce subshell :
  - s’arrête immédiatement en cas d’erreur grâce à `set -e` ;
  - vérifie que le fichier est lisible ;
  - refuse un secret placeholder ;
  - nettoie les variables héritées pertinentes ;
  - isole les variables chargées, qui disparaissent à la fin du subshell.

---

## 15. [2026-08-11] Contrat complet de la fonction `env_bool`

- **Module concerné :** `config/settings.py`
- **Symptômes / Recommandation :**
  La version initiale de `env_bool` documentait uniquement les valeurs considérées comme vraies :
  ```txt
  Valeurs acceptées : 1, true, yes, on.
  ```

  Le comportement attendu pour :
  - une valeur fausse ;
  - une valeur vide ;
  - une valeur invalide ;

  n’était pas documenté explicitement.
- **Cause :**
  Documentation incomplète du contrat de la fonction utilitaire.
- **Résolution :**
  Utiliser et documenter le contrat complet suivant :
  ```python
  def env_bool(name: str, default: bool = False) -> bool:
      """
      Interprète une variable d'environnement comme booléen.

      Valeurs vraies acceptées : 1, true, yes, on.
      Valeurs fausses acceptées : 0, false, no, off.

      Si la variable est absente ou vide, la valeur par défaut est retournée.
      Si la variable contient une valeur non booléenne, une exception
      ImproperlyConfigured est levée afin d'éviter une configuration ambiguë.
      """
      value = os.getenv(name)

      if value is None or not value.strip():
          return default

      normalized = value.strip().lower()

      if normalized in {"1", "true", "yes", "on"}:
          return True

      if normalized in {"0", "false", "no", "off"}:
          return False

      raise ImproperlyConfigured(
          f"La variable d'environnement {name} doit être un booléen valide."
      )
  ```

---

## 16. [2026-08-11] Validation finale après corrections

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

  La validation de production doit désormais être faite avec un environnement isolé, sans placeholder de secret, et avec `DEBUG=False`.

  ---
## 17. [2026-08-12] Finitions AUTH-034 : bloc `else` développement et validation CORS production
- **Ticket associé :** `AUTH-034` — Durcissement CORS / HTTPS
- **Symptômes :**
  1. Le bloc conditionnel `if not DEBUG:` dans `settings.py` n'avait pas de
     branche `else` explicite. En cas de variable `SECURE_*` injectée
     accidentellement dans l'environnement, le comportement en développement
     pouvait être ambigu.
  2. `CORS_ALLOWED_ORIGINS` n'était pas validé en production : une variable
     vide produisait silencieusement une liste vide sans erreur explicite.
- **Résolution :**
  1. Ajout d'un bloc `else` qui force explicitement :
     - `SECURE_SSL_REDIRECT = False`
     - `SESSION_COOKIE_SECURE = False`
     - `CSRF_COOKIE_SECURE = False`
     - `SECURE_HSTS_SECONDS = 0`
  2. Ajout d'une vérification fail-closed en production :
     ```python
     if not CORS_ALLOWED_ORIGINS:
         raise ImproperlyConfigured(
             "CORS_ALLOWED_ORIGINS est obligatoire en production."
         )
     ```
- **Validation :** `python manage.py test` → OK