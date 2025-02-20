web: python manage.py migrate && python manage.py collectstatic --no-input && gunicorn --timeout 300 --workers 2 --threads 4 --bind 0.0.0.0:$PORT myproject.wsgi
worker: python manage.py runserver_bot
