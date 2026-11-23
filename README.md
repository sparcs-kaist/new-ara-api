# Ara API

Restful API for Ara, KAIST's official community service

![Python version][badge/python-version]
[![Code style: black][badge/black]][repo/black]
[![Imports: isort][badge/isort]][isort]
[![pre-commit][badge/pre-commit]][repo/pre-commit]
[![Conventional Commits][badge/conventional-commits]][conventional-commits]

## Project Setup

Use Python 3.14.7 and [uv](https://docs.astral.sh/uv/getting-started/installation/)
0.13.9 for new setups. Container builds pin uv 0.13.9. Existing local installations
of uv `>=0.11.15,<0.14` can also use an already installed Python 3.14.7.
The project uses `.python-version`, `pyproject.toml`, and the committed `uv.lock`
for the Python interpreter, dependency policy, and exact resolved versions.

```bash
uv python install
uv sync --locked # Creates .venv, including development and test dependencies

# Run `pre-commit` automatically on `git commit`
uv run --locked pre-commit install
uv run --locked pre-commit install --hook-type commit-msg
```

## How to Run

```bash
docker compose -f docker-compose.local.yml up -d
make run
```

Configure `.env` for the services above before starting the API. For local
file logging, set `LOG_FILE_PATH=logs/http_access.log` and create `logs/`.
The Makefile runs Python commands through `uv run --locked`; activating a shell
is optional. Editors should use `.venv/bin/python`.

## Dependency changes

```bash
uv add 'package>=1,<2'              # Add a runtime dependency
uv add --group dev package         # Add a development tool
uv add --group test package        # Add a test dependency
uv remove package
uv lock --upgrade-package package  # Update one package within its allowed range
uv lock --upgrade                  # Update all packages within their allowed ranges
uv sync --locked
uv lock --check
```

Commit `pyproject.toml` and `uv.lock` together. Major upgrades require reviewing
the declared compatibility bounds as well as release notes. Production installs
use `uv sync --locked --no-dev`; test-only installs add `--group test`.
AWS CLI is an external tool rather than an application dependency; use AWS CLI
v2 or `uvx --from awscli aws` when needed.

The [dependency upgrade report](docs/dependency-upgrade.json) records previous
and locked versions, dependency group changes, validation and deployment follow-up.
Django stays on the 5.2 LTS patch series. The Elasticsearch libraries stay on 7.x
to match the existing server; their major upgrade requires a server and index
migration. `python-dateutil` stays below 3 to satisfy Botocore's requirements.
Weekly Dependabot updates cover uv dependencies, GitHub Actions and Docker;
Python dependency major upgrades remain deliberate compatibility changes.

## Tests

```bash
make test_docker      # Builds the test image and runs the isolated integration suite
make test_docker_down # Stops the test services
```

This environment has dedicated MySQL, Redis and Elasticsearch containers and uses
dummy credentials with Firebase disabled. It does not require production secrets.
Elasticsearch installs the Nori plugin on first startup and can take a few minutes.
On Apple Silicon the retained Elasticsearch 7.9.2 image runs under amd64 emulation.

For host-based tests, point the `NEWARA_*` variables at dedicated test services,
set `FCM_DISABLED=1` and a writable `LOG_FILE_PATH`, then run:

```bash
make i18n_compile
make test
```

Do not point tests at shared services: the fixtures clear application Redis keys
and rebuild the test search index. The test settings run Celery tasks eagerly.
To check the actual worker in the isolated environment:

```bash
docker compose -p newara-test -f docker-compose.test.yml --profile worker up -d celery
docker compose -p newara-test -f docker-compose.test.yml exec celery celery -A ara inspect ping
```

## Container builds

```bash
docker build --target production -t newara:production .
docker build --target development -t newara:development .
docker build --target test -t newara:test .
```

The default target is `production`. Development and test images extend the same
application layer, adding only their dependency groups. Supervisor, Gunicorn,
Daphne and Celery use the image's `.venv/bin` via `PATH`.

Environment files and Firebase service account keys are excluded from images.
Supply environment variables at runtime and mount the Firebase key read-only at
`/newara/www/firebaseServiceAccountKey.json` when push notifications are enabled.
CI tests the test image and checks the production image before publishing it.

Before deployment, verify migrations against a staging database, back up the
database, and retain the previous image digest. Apply migrations once, restart
the API and workers, and verify authentication, search, uploads, WebSockets,
scheduled tasks and queue processing. Reverting an image does not undo database
migrations; review schema compatibility before rolling back.

## URLs

- Base URL: `/api`
- Admin page: `/api/admin/`
- API documentations:
  - `/api/schema/swagger/`
  - `/api/schema/redoc/`

## Direct attachment uploads to S3

Use the existing Ara authentication for the start and completion requests.
The browser sends the file directly to S3 in one PUT.

1. `POST /api/attachments/uploads/` with `{"filename":"video.mp4","size":150000000}`.
   Use the browser's `File.name` and `File.size` in bytes. `alias` is optional.
   A `201` response contains `id`, `upload_url`, `headers`, and `expires_in`.
2. Use the returned URL and headers for the S3 request. Send the entire `File`
   as the request body. The browser supplies the signed `Content-Length`.

   ```js
   const put = await fetch(upload.upload_url, {
     method: "PUT",
     headers: upload.headers,
     body: file,
     credentials: "omit",
   });
   ```

3. After a successful PUT, send `POST /api/attachments/uploads/{id}/complete/`
   with an empty body. Use the returned `Attachment.id` in the existing article
   flow. Repeating completion after success returns the same attachment ID.

Start the PUT within the URL's 15-minute lifetime. A failed transfer can be
retried with the same URL while it is valid. The retry sends the entire file.
If S3 returns `412` on a retry, try completion because the first PUT may have
succeeded. If completion reports that the file is missing, retry the PUT.
Start a new session when the URL has expired and the file still needs uploading,
or when completion returns `410` after the 24-hour completion window.

Before enabling the frontend flow, run `python manage.py migrate`. Allow `PUT`
from the frontend origins in S3 CORS and allow the headers returned by the
start endpoint. The API role needs `s3:PutObject`, `s3:PutObjectAcl`,
`s3:PutObjectTagging`, `s3:GetObject`, and `s3:DeleteObjectTagging` for these
objects. `s3:ListBucket` lets S3 report an absent object as `404` during
completion. Configure an S3 lifecycle expiration rule for objects under
`files/direct-uploads/` tagged `ara-upload=pending`. Use a retention period
longer than the 24-hour completion window, such as 7 days. Completion removes
the tag before publishing the attachment. `ATTACHMENT_UPLOAD_MAX_BYTES` defaults
to 5 GiB and can be lowered for the deployment.

## How to Contribute

1. Follow [Conventional Commits][conventional-commits] for writing commit messages.
2. Use type hints strictly. (Check [PEP 484][pep-484].)

[badge/python-version]: https://img.shields.io/badge/python-3.14.7-blue
[badge/black]: https://img.shields.io/badge/code%20style-black-000000
[badge/isort]: https://img.shields.io/badge/%20imports-isort-%231674b1?labelColor=ef8336
[badge/pre-commit]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
[badge/conventional-commits]: https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white
[isort]: https://pycqa.github.io/isort
[conventional-commits]: https://conventionalcommits.org
[pep-484]: https://peps.python.org/pep-0484/
[repo/black]: https://github.com/psf/black
[repo/pre-commit]: https://github.com/pre-commit/pre-commit
