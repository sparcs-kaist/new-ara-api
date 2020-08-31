#!/bin/sh

set -ex

while ! nc -vz $NEWARA_DB_HOST $NEWARA_DB_PORT; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

if [ "$1" = "test" ]; then
    /newara/www/venv/bin/pytest tests --verbose
else
    venv/bin/python manage.py collectstatic --noinput
    venv/bin/python manage.py migrate --no-input
    venv/bin/python manage.py compilemessages -l en -l ko
    ln -s /newara/www/.docker/supervisor-app.conf /etc/supervisor/conf.d/ || true
    exec supervisord -n
fi
