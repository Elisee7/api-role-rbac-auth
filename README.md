# API Auth + Roles

API REST sécurisée d'authentification JWT (access + refresh) et de gestion des permissions par rôles (RBAC), avec documentation OpenAPI / Swagger.

> Conforme au cahier des charges « Auth + Roles » v1.0.

---

## ✨ Fonctionnalités

- **Authentification JWT** : inscription, connexion, rafraîchissement avec rotation, déconnexion (blacklist).
- **RBAC** : gestion des rôles et permissions, contrôle d'accès à l'exécution.
- **Profil utilisateur** : consultation et mise à jour de son propre profil.
- **Sécurité** : hachage PBKDF2, rate limiting, durcissement CORS / HTTPS.
- **Documentation** : Swagger UI interactive et schéma OpenAPI exportable.

---

## 🛠 Stack technique

| Composant | Technologie |
|---|---|
| Framework backend | Django 6.0.7 + Django REST Framework 3.17 |
| Authentification JWT | djangorestframework-simplejwt 5.5 (access + refresh + blacklist) |
| Base de données | PostgreSQL |
| Documentation API | drf-spectacular 0.30 (OpenAPI 3 / Swagger UI) |
| CORS | django-cors-headers 4.9 |
| Python | 3.12 |

---

## 📋 Prérequis

- Python **3.12**
- PostgreSQL **15+**
- `pip` et `venv`

---

## 🚀 Installation

```bash
# 1. Cloner le dépôt
git clone <url-du-repo> p1_v4_1_api_auth
cd p1_v4_1_api_auth/backend

# 2. Créer et activer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Copier le fichier d'exemple et renseigner les valeurs :

```bash
cp .env.example .env
```

| Variable | Description | Exemple |
|---|---|---|
| `DJANGO_ENV` | Environnement (`development` / `production`) | `development` |
| `DEBUG` | Mode debug (`True` uniquement en développement) | `True` |
| `DJANGO_SECRET_KEY` | Clé secrète (≥ 50 caractères, jamais commitée) | — |
| `ALLOWED_HOSTS` | Hôtes autorisés (séparés par virgule) | `localhost,127.0.0.1` |
| `CORS_ALLOWED_ORIGINS` | Origines CORS autorisées | `http://localhost:3000` |
| `DB_ENGINE` | Moteur de base de données | `django.db.backends.postgresql` |
| `DB_NAME` | Nom de la base | `auth_roles_db` |
| `DB_USER` | Utilisateur PostgreSQL | `postgres` |
| `DB_PASSWORD` | Mot de passe PostgreSQL | — |
| `DB_HOST` | Hôte PostgreSQL | `localhost` |
| `DB_PORT` | Port PostgreSQL | `5432` |
| `THROTTLE_AUTH_RATE` | Limite de débit des endpoints auth | `10/minute` |

Générer une clé secrète forte :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🗄️ Base de données

```bash
# Appliquer les migrations
python manage.py migrate

# Charger les rôles et permissions initiaux (ADMIN, MANAGER, USER)
python manage.py loaddata initial_roles

# Créer un superutilisateur (optionnel)
python manage.py createsuperuser
```

---

## ▶️ Lancement

```bash
python manage.py runserver
```

L'API est accessible sur `http://localhost:8000`.

---

## 📡 Endpoints principaux

| Méthode | Endpoint | Description | Accès |
|---|---|---|---|
| POST | `/api/auth/register/` | Inscription | Public |
| POST | `/api/auth/login/` | Connexion (access + refresh token) | Public |
| POST | `/api/auth/refresh/` | Rafraîchissement (avec rotation) | Refresh token valide |
| POST | `/api/auth/logout/` | Déconnexion (blacklist) | Authentifié |
| GET / PATCH | `/api/users/me/` | Profil de l'utilisateur connecté | Authentifié |
| POST | `/api/users/{id}/assign-role/` | Attribuer un rôle | Admin (`roles.manage`) |
| GET / POST / PUT / PATCH / DELETE | `/api/roles/` | CRUD des rôles | Admin (`roles.manage`) |
| GET | `/api/permissions/` | Liste des permissions | Admin (`roles.manage`) |

L'authentification se fait via l'en-tête :

```
Authorization: Bearer <access_token>
```

---

## 📚 Documentation Swagger

- **Swagger UI** : `http://localhost:8000/api/docs/`
- **Schéma OpenAPI** : `http://localhost:8000/api/schema/`

Régénérer le schéma versionné :

```bash
python manage.py spectacular --file schema.yml --validate
```

---

## 🧪 Tests

```bash
# Exécuter toute la suite de tests
python manage.py test

# Vérifier la cohérence du projet
python manage.py check

# Vérifier la configuration de déploiement
python manage.py check --deploy
```

La suite couvre les 5 scénarios critiques du cahier des charges :
1. Inscription d'un utilisateur
2. Connexion et émission des tokens
3. Rafraîchissement et rotation du token
4. Contrôle d'accès basé sur les rôles
5. Déconnexion et invalidation du refresh token

---

## 📁 Structure du projet

```
.
├── .github/workflows/ci.yml      # Pipeline CI (GitHub Actions)
├── backend/
│   ├── apps/
│   │   ├── accounts/             # Authentification & profil utilisateur
│   │   ├── api/                  # Routage global + composants OpenAPI
│   │   └── roles/                # Rôles & permissions (RBAC)
│   ├── config/                   # settings.py & urls.py
│   ├── docs/
│   │   ├── adr/                  # Décisions d'architecture (ADR)
│   │   └── security/             # Rapports de revue de sécurité
│   ├── .env                      # Variables d'environnement (non versionné)
│   ├── requirements.txt
│   └── schema.yml                # Schéma OpenAPI versionné
├── CHANGELOG.md
└── DEBUG_LOG.md
```

---

## 🔒 Sécurité

- Hachage des mots de passe via **PBKDF2** (défaut Django).
- **Rotation** du refresh token à chaque rafraîchissement + **blacklist**.
- **Rate limiting** sur les endpoints d'authentification (`/login`, `/refresh`, etc.).
- Configuration **CORS** restreinte aux origines autorisées.
- Durcissement **HTTPS / HSTS** activé automatiquement en production (`DEBUG=False`).

> ⚠️ Les fichiers `.env` et secrets ne doivent **jamais** être versionnés (cf. `.gitignore`).

---

## 📄 Documentation complémentaire

- **ADR 001** — Architecture et politique des jetons JWT : `backend/docs/adr/001-architecture-jwt.md`
- **Matrice rôles / permissions** : `backend/docs/roles-permissions-matrix.md`
- **Revue sécurité OWASP** : `backend/docs/security/auth-032-owasp-api-top10.md`
- **Journal de débogage** : `DEBUG_LOG.md`

---

## 📝 Licence

Projet interne — usage non commercial.