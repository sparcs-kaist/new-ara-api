FROM python:3.7

RUN pip install --upgrade pip virtualenv awscli
RUN virtualenv -p python3 /newara/www/venv

RUN apt-get update && apt-get install netcat-openbsd supervisor vim -y

ADD ./ /newara/www

WORKDIR /newara/www
RUN /newara/www/venv/bin/pip install poetry
RUN /newara/www/venv/bin/poetry export -f requirements.txt | venv/bin/pip install -r /dev/stdin

RUN mkdir -p /var/log/newara/
RUN chmod +x /newara/www/.docker/run.sh
RUN chmod +x /newara/www/.docker/run-celery.sh

EXPOSE 9000
