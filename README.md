# SPARCS NewAra API

<p align="center">
  <img src="https://raw.githubusercontent.com/sparcs-kaist/new-ara-web/master/src/assets/Services-Ara.png" alt="Logo" height="150">
</p>

Restful API for NewAra @ SPARCS

## Project Stack

### Interpreter

* `Python 3.7`
* ~~`pip 19.2`~~
* `poetry` is used as package manager

### Framework

* `Django 2.2`
* `djangorestframework 3.10`

### Database

* MySQL (default)
* `mysqlclient 1.4`
* `django-mysql 3.2`

Works with MySQL for Linux & macOS, not tested in Windows. Timezone is automatically adjusted. It is strongly recommended to set default charset of database or MySQL server to `utf8mb4`.

### Storage

* AWS S3
* `django-s3-storage 0.12`

Two buckets are used - one for storing static files, one for media files that users upload. Go to django-s3-storage documentation for required permissions.

Also, you can find `docker-compser.yml` in `sparcs-newara` AWS S3 bucket.

### Authentication

* SPARCS SSO v2 API
* `djangorestframework TokenAuthentication`

### API Documentation

* `drf-yasg 1.16`

> Miscellaneous packages are listed in `requirements.txt`.

## Project Setup

### Create & Activate Virtual Environment

```bash
$ python3 -m venv env
$ source env/bin/activate
```

### Install Requirements

```bash
$ pip install poetry
$ poetry install # in production - $ poetry install --no-dev
```

For macOS, you may need to install `openssl` & `mysqlclient` and set `LDFLAGS=-L/usr/local/opt/openssl/lib` before installing requirements. Only tested for macOS Mojave. See [link](https://stackoverflow.com/questions/50940302/installing-mysql-python-causes-command-clang-failed-with-exit-status-1-on-mac).

For Ubuntu, you may need to install `make`, `mysqlclient`, `autoenv`.

### Fill Environment Configuration

Refer to `.env.example` file to make `.env` file in cloned directory and fill in the required informations. For SPARCS SSO, create a test service or ask SYSOP to deploy production server.

### Flush and Migrate Database 

If you have successfully installed `mysqlclient`, make sure that `root` does not have a password, and run

```
$ make flush
$ make migrate
```

In case `make flush` returns `Can't drop database 'new_ara'; database doesn't exist` error, you can solve this by either modifying `flush` command in `Makefile` or creating empty database `new_ara` after running `mysql`.

`migrate` command creates required tables in the database. You also need to `makemigrations` & `migrate` if you changed the models - Django will alter tables for you.

After, run

```
$ cd new-ara-api
$ echo 'source ~/.autoenv/activate.sh' >> ~/.bashrc
```

`autoenv` will now automatically set virtualenv when you move to the specified directory. 


### Collect static files

```bash
$ python manage.py collectstatic
```

`collectstatic` command collects all static files required to run installed apps to selected storage - for this project, static S3 bucket. You should open public access for the static bucket to get appropriate response.

### Run lightweight server for development

```bash
$ python manage.py runserver 0:<port>
```

`0` is abbreviation for `0.0.0.0` which refers to 'listening to every incoming hosts'. **Do not deploy with runserver command - use WSGI. This command is only for development.**

## Deployment

### uWSGI

~~WIP~~

### Celery

~~WIP~~

## Contributors

See [contributors](https://github.com/sparcs-kaist/new-ara-api/graphs/contributors).
