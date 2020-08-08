#!/bin/sh

set -ex

while ! nc -vz $NEWARA_DB_HOST $NEWARA_DB_PORT; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

venv/bin/python manage.py migrate --no-input
venv/bin/gunicorn -b 0.0.0.0:9000 ara.wsgi:application
