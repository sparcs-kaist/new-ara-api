# SPARCS NewAra API
<br />
<br />
<br />
<p align="center">
  <a href="https://newara.sparcs.org">
    <img src="https://raw.githubusercontent.com/sparcs-kaist/new-ara-web/master/src/assets/Services-Ara.png" alt="Logo" height="150">
  </a>
  
  <p align="center">
    <img src="https://img.shields.io/badge/version-1.1-informational.svg" />
    <img src="https://img.shields.io/badge/license-MIT-black.svg" />
  </p>
  
  <p align="center">
    Restful API for NewAra @ SPARCS
    <br />
    KAIST 공식 학내 커뮤니티
    <br />
    <a href="https://newara.sparcs.org">Go to ARA</a>
  </p>
</p>

## Management Information
- Issue tracking: Notion
- Credentials: S3 sparcs-credentials
- Communication: Slack
  - general: #new-ara
  - backend: #new-ara-backend
  - fontend: #new-ara-frontend
  - github commits: #new-ara-noti
  - sentry alerts: #new-ara-sentry
  - notion changes: #new-ara-notion
  - with OB: #ara
- Contact: new-ara@sparcs.org

<br />
<br />

## Project Setup

### Create & Activate Virtual Environment

```bash
$ python3 -m venv env  # should be python 3.8
$ source env/bin/activate
```

### Install Requirements

```bash
$ pip install poetry
$ poetry install # in production - $ poetry install --no-dev
```

For macOS, you may need to install `openssl` & `mysqlclient` and set `LDFLAGS=-L/usr/local/opt/openssl/lib` before installing requirements. Only tested for macOS Mojave. See [link](https://stackoverflow.com/questions/50940302/installing-mysql-python-causes-command-clang-failed-with-exit-status-1-on-mac).

### Fill Environment Configuration

Refer to  [.env.example file](https://github.com/sparcs-kaist/new-ara-api/blob/master/.env.example) and write your own `.env` file with required informations filled-in. For SPARCS SSO, create a test service or ask SYSOP to deploy production server.

For the test service in [SPARCS SSO](https://sparcssso.kaist.ac.kr/) for local settings, fill in as below.
- **Main URL**: (can be anything)
- **Login Callback URL**: http://127.0.0.1:9000/api/users/sso_login_callback/
- **Unregister URL**: http://127.0.0.1:9000/api/users/sso_unregister/

After this, you should make the information in the `.env` file as environment variables for local run. (In development or porduction server, we do not use `.env` file. Rather, we use environment variables in `docker-compose.yml` file.)

To make the make the information in the `.env` file as environment variables for local run, you can export each manually, or you can use the below command. Check the `Makefile`'s [env command](https://github.com/sparcs-kaist/new-ara-api/blob/master/Makefile#L32) and revise it. The command is written assuming you are using `~/.bashrc`. You might want to revise it to `~/.bash_profile` or `~/.zshrc` according to your settings.
```bash
$ make env
```

### :heart: Useful Commands:heart:
Most useful commands are already written in the [Makefile](https://github.com/sparcs-kaist/new-ara-api/blob/master/Makefile).
Refer to the `Makefile` and try to understand and use them.

### Create and Migrate Database

```bash
$ make init
```

### Collect static files

```bash
$ python manage.py collectstatic
```

`collectstatic` command collects all static files required to run installed apps to selected storage - for this project, static S3 bucket. You should open public access for the static bucket to get appropriate response.

### Internationalization (i18n)
[xgettext](https://man7.org/linux/man-pages/man1/xgettext.1.html) is required in order to generate translation files.
Detailed background on this can be found on [Django's documentations](https://docs.djangoproject.com/en/3.1/topics/i18n/translation/).
To generate translation files, run:
```bash
$ make i18n_generate
```
Translation files are generated under `ara/locale/(Locale name)/LC_MESSAGES`.
After writing translations, run the following command to apply the translations.
```bash
$ make i18n_compile
```

### Create log directory
```bash
$ sudo mkdir -p /var/log/newara
$ sudo chown $(whoami) /var/log/newara
```

### Run lightweight server for development

```bash
$ make run
```

`0` is abbreviation for `0.0.0.0` which refers to 'listening to every incoming hosts'. **Do not deploy with runserver command - use WSGI. This command is only for development.**

---

## Deployment with Docker

### docker-compose.yml
`docker-compose.yml` file is managed in S3 `sparcs-newara` bucket `docker-compose` directory. For simple local deployment, refer to [docker-compose.example.yml file](https://github.com/sparcs-kaist/new-ara-api/blob/master/docker-compose.example.yml) and fill in the information needed.

For [development server](https://newara.dev.sparcs.org/), two docker containsers are up with the docker-compose file. Using AWS RDS for mysql, elastiCache for redis.
- api container (used gunicorn for serving. celery-beat also here.)
- celery-worker container

### docker image
For managing docker images, we are using AWS ECR, `newara` repository.
- Using tag `newara:dev` for development server.

### other docker related files
- **Dockerfile**: We use virtual environment also inside the docker container.
- **.docker/run.sh**: api container's entrypoint.
- **.docker/run-celery.sh**: celery worker container's entrypoint.
- **.docker/supervisor-app.conf**
- **.docker/supervisor-celery-worker.conf**

<br />
<br />

## Project Stack

### Interpreter

* `Python 3.7`
* `poetry` is used as package manager
  * When adding libraries to the virtual environment, you should not use `pip`. Rather, use `poetry add` command. Refer to [this link](https://python-poetry.org/docs/cli/) for poetry  commands.

### Framework

* `Django 3.1`
* `djangorestframework 3.10`

### Database

* MySQL (default)
* `mysqlclient 2.0`
* `django-mysql 3.2`

Works with MySQL for Linux & macOS, not tested in Windows. Timezone is automatically adjusted. It is strongly recommended to set default charset of database or MySQL server to `utf8mb4`.

### Storage

* AWS S3
* `django-s3-storage 0.12`

Two buckets are used - one for storing static files, one for media files that users upload. Go to django-s3-storage documentation for required permissions.

### Authentication

* SPARCS SSO v2 API
* `djangorestframework SessionAuthentication`

### API Documentation

* `drf-yasg 1.17`

---

## Contributors

See [contributors](https://github.com/sparcs-kaist/new-ara-api/graphs/contributors).
