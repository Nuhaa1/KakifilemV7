web: python manage.py collectstatic --noinput && gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT & python manage.py runserver_bot & wait -n
