#!/bin/sh
set -e

echo "Running migrations..."
uv run python manage.py migrate --noinput

echo "Starting gunicorn..."
exec uv run gunicorn retirement_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120
