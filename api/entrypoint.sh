#!/bin/bash

# Fix permissions on mounted volumes for Foundry operations
# This allows the radar user to create directories in /radar_data
if [ -d "/radar_data" ]; then
    find /radar_data -type d -exec chmod 777 {} \; 2>/dev/null || true
fi

poetry run python manage.py collectstatic --no-input
poetry run python manage.py makemigrations --no-input || { echo 'makemigrations failed' ; exit 1; }
poetry run python manage.py migrate --no-input || { echo 'migrate failed' ; exit 1; }
poetry run python manage.py createsuperuser --noinput --email ""

poetry run gunicorn --bind 0.0.0.0:8000 api.wsgi:application
