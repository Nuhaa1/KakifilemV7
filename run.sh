#!/bin/bash

# Run migrations and collect static files
python manage.py migrate
python manage.py collectstatic --noinput

# Start the Django server and bot together
(gunicorn myproject.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --worker-class=gevent --timeout 0) & \
(python manage.py runserver_bot) &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
