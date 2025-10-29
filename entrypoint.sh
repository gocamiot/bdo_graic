#!/bin/sh

# entrypoint.sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Collect static files
echo "Collecting static files"
python manage.py collectstatic --noinput

# Apply database migrations
echo "Applying database migrations"
python manage.py makemigrations
yes | python manage.py makemigrations --merge
#python manage.py migrate home --fake-initial
python manage.py migrate

# Start server
echo "Starting server"
exec gunicorn --reload core.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 1200
