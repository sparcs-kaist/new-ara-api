FROM python:3.6

LABEL Name=new-ara-api Version=0.0.1
EXPOSE 8080

WORKDIR /srv
COPY . /srv

RUN pip install -r requirements.txt

RUN python ara/manage.py migrate
RUN python ara/manage.py collectstatic --no-input

CMD ["uwsgi", "--http", "0.0.0.0:8080", "--chdir", "/srv/ara", "--module", "ara.wsgi:application"]

