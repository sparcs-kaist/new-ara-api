FROM python:3.11

RUN apt update && apt install netcat-openbsd supervisor gettext -y

WORKDIR /newara/www

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/log/newara/
RUN chmod +x /newara/www/.docker/run.sh
RUN chmod +x /newara/www/.docker/run-celery.sh

EXPOSE 9000
