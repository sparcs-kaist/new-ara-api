#!/bin/sh

set -ex

while ! nc -vz $NEWARA_DB_HOST $NEWARA_DB_PORT; do
  >&2 echo "MySQL is unavailable - sleeping"
  sleep 1
done

sleep 5

while ! nc -vz $NEWARA_REDIS_ADDRESS 6379; do
  >&2 echo "Redis is unavailable - sleeping"
  sleep 1
done

ln -s /newara/www/.docker/supervisor-celery-worker.conf /etc/supervisor/conf.d/ || true

exec supervisord -n
