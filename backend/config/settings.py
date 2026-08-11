import os
from pathlib import Path
from dotenv import load_dotenv, dotenv_values
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

def resolve_environment() -> str:
    """
    Résout l'environnement d'exécution sans charger aveuglément le fichier .env.

    Règles :
    - La variable d'environnement DJANGO_ENV du processus est prioritaire.
    - Si elle est absente, on lit uniquement DJANGO_ENV dans .env via dotenv_values(),
      sans injecter les autres variables du fichier dans l'environnement.
    - Si l'environnement est 'development', le fichier .env local peut être chargé.
    - Si l'environnement est 'production', le fichier .env local ne doit pas être chargé.
      Les variables de production doivent provenir de l'environnement d'exécution
      ou d'un fichier de configuration production chargé volontairement.
    """
    env_value = os.getenv("DJANGO_ENV")

    # Si DJANGO_ENV n'est pas déjà fourni par l'environnement du processus,
    # on consulte seulement la valeur DJANGO_ENV du fichier .env local.
    if not env_value:
        env_file = BASE_DIR / ".env"

        if env_file.is_file():
            env_value = dotenv_values(env_file).get("DJANGO_ENV")

    if not env_value:
        raise ImproperlyConfigured(
            "DJANGO_ENV est absent. "
            "Définissez DJANGO_ENV=development ou DJANGO_ENV=production."
        )

    normalized = env_value.strip().lower()

    if normalized not in {"development", "production"}:
        raise ImproperlyConfigured(
            f"Valeur DJANGO_ENV invalide : {env_value!r}. "
            "Attendu : 'development' ou 'production'."
        )

    return normalized


DJANGO_ENV = resolve_environment()

# Chargement complet du fichier .env local uniquement en développement.
if DJANGO_ENV == "development":
    load_dotenv(BASE_DIR / ".env", override=False)


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

# Quick-start development settings - unsuitable for production 
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

"""
Sécurité : SECRET_KEY.

La clé secrète doit être fournie par variable d'environnement.
Elle ne doit jamais être codée en dur ni commitée avec une vraie valeur.
"""
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise ImproperlyConfigured(
        "La variable d'environnement DJANGO_SECRET_KEY est obligatoire."
    )

"""
Mode debug.

Doit être True uniquement en développement local.
Doit être False en staging et production.
"""
DEBUG = env_bool("DEBUG", default=False)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "La variable d'environnement ALLOWED_HOSTS est obligatoire."
    )

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'apps.accounts',
    'apps.api',
    'apps.roles',

    # Apps tiers
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist', # Pour la gestion de la blacklist
    "corsheaders",
    "drf_spectacular",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
"""
Description : Configuration de la base de données PostgreSQL.
"""

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}

# Vérification explicite des variables obligatoires
REQUIRED_DB_VARS = ["DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"]

missing_db_vars = [var for var in REQUIRED_DB_VARS if not os.getenv(var)]

if missing_db_vars:
    raise ImproperlyConfigured(
        f"Variables d'environnement manquantes : {', '.join(missing_db_vars)}"
    )


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'fr'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Africa/Ouagadougou'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Modèle d'utilisateur personnalisé
AUTH_USER_MODEL = 'accounts.CustomUser'

"""
Description : Configuration JWT (durées de vie, rotation et blacklist).
"""
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        # Limitation des endpoints d'authentification sensibles
        "auth": os.getenv("THROTTLE_AUTH_RATE", "10/minute"),
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


SIMPLE_JWT = {
    # Durées de vie des jetons
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),   # CDC 5.2 : Courte durée[cite: 1]
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),       # CDC 5.2 : Longue durée[cite: 1]

    # Sécurité & Invalidation
    'ROTATE_REFRESH_TOKENS': True,                     # CDC 5.2 : Nouveau refresh token à chaque rafraîchissement[cite: 1]
    'BLACKLIST_AFTER_ROTATION': True,                  # CDC 5.2 : Invalide l'ancien refresh token[cite: 1]
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,

    # En-têtes HTTP
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),

    'TOKEN_OBTAIN_SERIALIZER': 'apps.accounts.serializers.CustomTokenObtainPairSerializer',
}

CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]

# En développement, on peut autoriser explicitement des origines locales.
# En production, la variable CORS_ALLOWED_ORIGINS doit être définie.
CORS_ALLOW_CREDENTIALS = False

"""
Durcissement de sécurité pour la production.

Ces réglages sont activés uniquement lorsque DEBUG=False.
Ils ne doivent pas être utilisés tels quels en développement local HTTP,
car ils peuvent casser l'accès local (redirection HTTPS, cookies secure, etc.).
"""
if not DEBUG:
    # Redirige toutes les requêtes HTTP vers HTTPS.
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=True)

    # Cookies sécurisés.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HTTP Strict Transport Security.
    # Commencer par une durée courte, puis augmenter après validation.
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "3600"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
        "SECURE_HSTS_INCLUDE_SUBDOMAINS",
        default=True
    )
    SECURE_HSTS_PRELOAD = env_bool(
        "SECURE_HSTS_PRELOAD",
        default=False
    )

    # Derrière un reverse proxy (Nginx, Traefik, Render, Railway, etc.),
    # Django doit pouvoir détecter le protocole original via X-Forwarded-Proto.
    if env_bool("SECURE_PROXY_SSL_HEADER", default=False):
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SPECTACULAR_SETTINGS = {
    "TITLE": "API Auth + Roles",
    "DESCRIPTION": (
        "API d'authentification JWT avec gestion des rôles et permissions. "
        "Conforme au cahier des charges Auth + Roles v1.0."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Auth", "description": "Inscription, connexion, refresh et logout"},
        {"name": "Users", "description": "Profil utilisateur"},
        {"name": "Roles", "description": "Gestion des rôles et permissions"},
    ],
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
    },
}