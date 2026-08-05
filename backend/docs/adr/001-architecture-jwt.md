# ADR 001 : Architecture et politique des jetons JWT

* **Statut** : Accepté
* **Date** : 2026-08-05
* **Auteur** : Elisha (Chef de projet technique)

## Contexte
L'API nécessite un système d'authentification stateless réutilisable pour le web et le mobile, garantissant un niveau de sécurité élevé tout en maintenant une expérience utilisateur fluide.

## Décisions prises

1. **Durée de vie des tokens** :
   * **Access Token** : Expire après **15 minutes** pour réduire la fenêtre de vulnérabilité en cas de vol de jeton.
   * **Refresh Token** : Expire après **7 jours** pour éviter une reconnexion trop fréquente de l'utilisateur.

2. **Rotation des jetons (Token Rotation)** :
   * Chaque appel à `/api/auth/refresh/` réinvalide l'ancien `refresh_token` et en génère un nouveau.

3. **Liste noire (Blacklist)** :
   * L'activation du module `token_blacklist` permet l'invalidation immédiate des tokens révoqués lors de la déconnexion (`/logout`) ou après rotation.

4. **Stockage recommandé côté client** :
   * Les clients frontend (ex: Next.js) doivent idéalement stocker le `refresh_token` dans un cookie sécurisé `httpOnly` afin de prévenir les attaques XSS.

## Conséquences
* **Positives** : Durcissement de la sécurité, invalidation possible à la déconnexion, conformité aux spécifications OWASP.
* **Négatives** : Requiert une écriture en base de données PostgreSQL pour enregistrer les tokens révoqués dans la blacklist.