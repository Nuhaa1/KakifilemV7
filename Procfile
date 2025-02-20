web: gunicorn myproject.wsgi:application --bind=0.0.0.0:$PORT --workers=2 --threads=4 --worker-class=gevent --timeout=0 --keep-alive=60 --log-level=info --max-requests=1000 --preload --access-logfile=- --error-logfile=- & python manage.py runserver_bot & wait -n
release: python manage.py migrate && python manage.py collectstatic --noinput
