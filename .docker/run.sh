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

while ! nc -vz $NEWARA_ELASTICSEARCH_HOST $NEWARA_ELASTICSEARCH_PORT; do
  >&2 echo "Elasticsearch is unavailable - sleeping"
  sleep 1
done


if [ "$1" = "test" ]; then
    python3 manage.py compilemessages -l en -l ko
    pytest tests --verbose
else
    python3 manage.py collectstatic --noinput
    python3 manage.py migrate --no-input
    python3 manage.py compilemessages -l en -l ko
    ln -s /newara/www/.docker/supervisor-app.conf /etc/supervisor/conf.d/ || true
    exec supervisord -n
fi
