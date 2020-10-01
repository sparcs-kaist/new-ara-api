#!/bin/sh

set -ex

while ! nc -vz $NEWARA_DB_HOST $NEWARA_DB_PORT; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

while ! nc -vz $NEWARA_REDIS_ADDRESS 6379; do
  >&2 echo "Redis is unavailable - sleeping"
  sleep 1
done

while ! nc -vz $NEWARA_ELASTICSEARCH_HOST 9200; do
  >&2 echo "Elasticsearch is unavailable - sleeping"
  sleep 1
done


if [ "$1" = "test" ]; then
    venv/bin/python manage.py compilemessages -l en -l ko
    venv/bin/pytest tests --verbose
else
    venv/bin/python manage.py collectstatic --noinput
    venv/bin/python manage.py migrate --no-input
    venv/bin/python manage.py compilemessages -l en -l ko
    ln -s /newara/www/.docker/supervisor-app.conf /etc/supervisor/conf.d/ || true
    exec supervisord -n
fi
