pip freeze > requirements.txt

python manage.py makemigrations 

python manage.py migrate

sudo -u postgres psql

python manage.py createsuperuser

python manage.py dbshell # se connecter a la bd oubien psql -U auth_user -d auth_roles_db -h localhost

\dt # afficher la liste des tables

\d : Pour voir les colonnes et la structure d'une table spécifique

pip install djangorestframework-simplejwt

