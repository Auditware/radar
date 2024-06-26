#!/bin/bash
poetry run python manage.py collectstatic --no-input
poetry run python manage.py makemigrations --no-input
poetry run python manage.py migrate --no-input
poetry run python manage.py createsuperuser --noinput --email ""

poetry run gunicorn --bind 0.0.0.0:8000 api.wsgi:application