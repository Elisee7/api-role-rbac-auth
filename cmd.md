# Commandes de déploiement et gestion du projet

## Dépendances
```bash
# Générer le fichier requirements.txt
pip freeze > requirements.txt
```

## Base de données - Migrations
```bash
# Créer les migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate
```

## Base de données - Accès PostgreSQL
```bash
# Se connecter en tant qu'utilisateur postgres (admin)
sudo -u postgres psql

# Ou se connecter via Django dbshell
python manage.py dbshell

# Ou connexion directe avec utilisateur dédié
psql -U auth_user -d auth_roles_db -h localhost
```

## Commandes PostgreSQL utiles
```sql
-- Lister toutes les tables
\dt

-- Voir la structure d'une table spécifique
\d nom_table

-- Quitter psql
\q
```

## Utilisateur administrateur
```bash
# Créer un superutilisateur Django
python manage.py createsuperuser
```

## Tests
```bash
# Exécuter les tests pour le module accounts
python manage.py test apps.accounts
```

## Authentification JWT
```bash
# Installer djangorestframework-simplejwt
pip install djangorestframework-simplejwt
```

## Données initiales (fixtures)
```bash
# Charger les rôles initiaux depuis apps/roles/fixtures/initial_roles.json
python manage.py loaddata initial_roles
```

## Ordre d'exécution recommandé
1. `pip freeze > requirements.txt`
2. `python manage.py makemigrations`
3. `python manage.py migrate`
4. `python manage.py createsuperuser`
5. `python manage.py test apps.accounts`  # Nouvelle étape
6. `python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'`  # Générer une clé secrète
7. `pip install djangorestframework-simplejwt`
8. `python manage.py loaddata initial_roles`
9. Vérification optionnelle : `python manage.py dbshell` puis `\dt`

## Site utile
- Décode le payload localement. Ne colle jamais un jeton d'accès réel sur un service tiers.
- Si jwt.io est nécessaire, utilise uniquement un jeton de test sans privilèges ni données sensibles.