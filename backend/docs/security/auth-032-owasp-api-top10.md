# AUTH-032 — Revue de sécurité OWASP API Top 10

## 1. Périmètre

Endpoints audités :
- /api/auth/register/
- /api/auth/login/
- /api/auth/refresh/
- /api/auth/logout/
- /api/users/me/
- /api/roles/
- /api/roles/{id}/
- /api/permissions/
- /api/permissions/{id}/
- /api/users/{id}/assign-role/

## 2. Méthodologie

Revue statique du code, de la configuration et des tests.
Référence : OWASP API Security Top 10.

## 3. Synthèse

| Gravité | Nombre |
|---|---|
| Bloquant | 0 |
| Majeur | 0 |
| Mineur | 0 |

## 4. Constats détaillés

### API1 — Broken Object Level Authorization

...

### API2 — Broken Authentication

...

## 5. Corrections appliquées

...

## 6. Actions différées

...

## 7. Validation

- python manage.py test
- python manage.py check
- python manage.py spectacular --file schema.yml --validate