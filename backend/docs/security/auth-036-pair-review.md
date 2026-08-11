# AUTH-036 — Audit croisé de sécurité (pair review)

> **Statut** : Terminé
> **Date** : 2026-08-11
> **Auteur** : Assistant (revue indépendante)
> **Référence** : OWASP API Security Top 10 (2023) — second regard
> **Complément à** : AUTH-032 (revue OWASP initiale)

---

## 1. Objectif

Apporter un second avis indépendant sur les points sensibles,
en se concentrant sur ce que la première revue (AUTH-032)
n'a pas couvert ou a pu sous-estimer.

## 2. Synthèse

| Gravité | Nombre | Détail |
|---------|-------:|--------|
| Bloquant | 0 | — |
| Majeur | 1 | Cache rate limiting (prod) |
| Mineur | 2 | Claim "role" figé, CORS vs ADR 001 |

---

## 3. Constats nouveaux

### 3.1 [MAJEUR] Cache par défaut : rate limiting inefficace en production multi-workers

**Constat :**
`settings.py` ne définit pas de bloc `CACHES`. Django utilise donc
`LocMemCache` (mémoire locale au processus). Or le rate limiting
(AUTH-033, `ScopedRateThrottle`) s'appuie sur ce cache.

**Impact :**
En production avec plusieurs workers (Gunicorn/uWSGI), chaque worker
possède son propre cache en mémoire. Un attaquant peut contourner la
limite en répartissant ses requêtes sur les workers → le contrôle
anti-brute-force devient inefficace.

**Note :** la blacklist SimpleJWT utilise la base de données
(tables `token_blacklist_*`), elle n'est PAS affectée.

**Recommandation (Sprint 5, prérequis déploiement) :**
Configurer un cache partagé (Redis) via la variable d'environnement
et ajouter `django-redis` aux dépendances de production.

---

### 3.2 [MINEUR] Claim "role" figé dans le JWT

**Constat :**
`CustomTokenObtainPairSerializer.get_token()` injecte le rôle dans
le claim. Si un admin change le rôle d'un utilisateur via
`/api/users/{id}/assign-role/`, l'access token déjà émis conserve
l'ancien rôle jusqu'à expiration (15 min).

**Impact :** Fenêtre de risque limitée à 15 min. Inhérent à
l'architecture stateless JWT (cf. ADR 001).

**Recommandation :** Documenter cette limitation dans l'ADR 001.
Acceptable en l'état.

---

### 3.3 [MINEUR] Incohérence `CORS_ALLOW_CREDENTIALS` vs ADR 001

**Constat :**
`settings.py` définit `CORS_ALLOW_CREDENTIALS = False`. Or l'ADR 001
recommande de stocker le refresh token dans un cookie `httpOnly`.
Avec `CORS_ALLOW_CREDENTIALS = False`, l'envoi de cookies cross-origin
est bloqué.

**Impact :** Incohérence entre la recommandation ADR et la config.
L'implémentation actuelle transmet le refresh token dans le body JSON,
donc `False` est techniquement correct. Mais la reco ADR n'est pas
applicable en l'état.

**Recommandation :** Clarifier l'ADR 001 (soit adopter le cookie +
`CORS_ALLOW_CREDENTIALS=True`, soit confirmer le body JSON).

---

## 4. Confirmation des points critiques (non-régression)

| Point | Vérification | Verdict |
|-------|-------------|---------|
| BOLA sur `/api/users/me/` | `get_object()` retourne `request.user` | ✅ Conforme |
| Énumération d'utilisateurs (login) | Message générique "No active account found..." | ✅ Conforme |
| Hachage mots de passe | PBKDF2 via Django, jamais en clair | ✅ Conforme |
| Rotation + blacklist | `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` actifs | ✅ Conforme |
| Rate limiting présent | `throttle_scope = "auth"` sur register/login/refresh/logout | ✅ Présent |
| Longueur clé secrète | `DJANGO_SECRET_KEY` doit mesurer au moins 32 octets (256 bits) après encodage UTF-8 ; vérifier `len(secret.encode('utf-8')) >= 32` et que la clé est générée aléatoirement (ex. `get_random_secret_key()`) sans jamais exposer la valeur | ✅ Conforme |
| `SECURE_PROXY_SSL_HEADER` conditionnel | Activé uniquement si variable explicite | ✅ Conforme |
| Headers sécurité Django 6 | `Content-Type nosniff`, `X-Frame DENY`, `Referrer-Policy` par défaut | ✅ Conforme |

---

## 5. Recommandations priorisées

| # | Action | Priorité | Échéance |
|---|--------|----------|----------|
| 1 | Configurer cache partagé (Redis) pour rate limiting | Haute | Sprint 5 (AUTH-041) |
| 2 | Documenter limitation claim "role" dans ADR 001 | Basse | Clôture |
| 3 | Clarifier CORS vs cookie httpOnly dans ADR 001 | Basse | Clôture |

---

## 6. Suivi des recommandations — Sprint 5

| # | Recommandation | Ticket Sprint 5 | Priorité | Statut |
|---|----------------|-----------------|----------|--------|
| 1 | Configurer cache partagé (Redis) pour rate limiting | **AUTH-041** (Déploiement staging) | Haute | ⏳ À faire |
| 2 | Documenter limitation claim `role` figé dans ADR 001 | **AUTH-045** (Rapport de fin de projet) | Basse | ⏳ À faire |
| 3 | Clarifier CORS vs cookie httpOnly dans ADR 001 | **AUTH-045** (Rapport de fin de projet) | Basse | ⏳ À faire |

> **Rappel :** Le point 1 est un **prérequis bloquant** pour AUTH-041.
> Les points 2 et 3 sont des actions de documentation à intégrer
> dans la rédaction du rapport de fin de projet (AUTH-045).
>
> **Note historique validée :** le dépôt contient déjà un `.gitignore` racine,
> et `backend/.env` n'est pas suivi par Git. Le constat "absence de `.gitignore`"
> correspond donc à un état antérieur, et il n'est plus comptabilisé comme
> constat majeur actif.