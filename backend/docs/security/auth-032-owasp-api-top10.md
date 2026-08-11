# AUTH-032 — Revue de sécurité OWASP API Top 10

> **Statut** : Terminé
> **Date** : 2026-08-11
> **Auteur** : Elisha (NIKIEMA Windkouni Elisée)
> **Référence** : OWASP API Security Top 10 (2023)
> **Périmètre** : API Auth + Roles v1.0

---

## 1. Périmètre

Endpoints audités :

| Méthode | Endpoint | Accès |
|---------|----------|-------|
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/auth/refresh/` | Refresh token valide |
| POST | `/api/auth/logout/` | Authentifié |
| GET | `/api/users/me/` | Authentifié |
| PATCH | `/api/users/me/` | Authentifié |
| GET | `/api/roles/` | Admin (`roles.manage`) |
| POST | `/api/roles/` | Admin (`roles.manage`) |
| PUT | `/api/roles/{id}/` | Admin (`roles.manage`) |
| PATCH | `/api/roles/{id}/` | Admin (`roles.manage`) |
| DELETE | `/api/roles/{id}/` | Admin (`roles.manage`) |
| GET | `/api/permissions/` | Admin (`roles.manage`) |
| GET | `/api/permissions/{id}/` | Admin (`roles.manage`) |
| POST | `/api/users/{id}/assign-role/` | Admin (`roles.manage`) |

---

## 2. Méthodologie

Revue statique du code source, de la configuration et de la suite de tests automatisés.

**Outils et fichiers inspectés :**
- `backend/apps/accounts/views.py` — vues d'authentification
- `backend/apps/accounts/serializers.py` — sérialiseurs
- `backend/apps/roles/views.py` — vues RBAC
- `backend/apps/roles/permissions.py` — classe de permission
- `backend/config/settings.py` — configuration sécurité
- `backend/apps/accounts/tests.py` — tests d'authentification
- `backend/apps/roles/tests.py` — tests RBAC
- `backend/schema.yml` — contrat OpenAPI

**Référence** : OWASP API Security Top 10 (édition 2023).

---

## 3. Synthèse

| Gravité | Nombre | Détail |
|---------|-------:|--------|
| Bloquant | 0 | — |
| Majeur | 0 | — |
| Mineur | 2 | API4 (pagination), API8 (exposition Swagger) |

---

## 4. Constats détaillés

---

### API1 — Broken Object Level Authorization (BOLA)

**Évaluation** : ✅ Conforme

**Analyse :**

| Endpoint | Mécanisme de protection | Verdict |
|----------|------------------------|---------|
| `/api/users/me/` | `get_object()` retourne `request.user` | Aucun accès à un autre utilisateur possible |
| `/api/users/{id}/assign-role/` | Protégé par `HasRolePermission` + `roles.manage` | Seul un admin peut cibler un autre utilisateur |
| `/api/roles/{id}/` | Protégé par `HasRolePermission` + `roles.manage` | CRUD rôles réservé aux admins |
| `/api/permissions/{id}/` | Protégé par `HasRolePermission` + `roles.manage` | Lecture réservée aux admins |

**Preuve dans le code :**

```python
# apps/accounts/views.py — UserMeView
def get_object(self):
    # Récupère directement l'utilisateur lié au Token JWT
    return self.request.user 