# Ara API

Restful API for Ara, KAIST's official community service

![GitHub Pipenv locked Python version (master)][badge/python-version]
[![Code style: black][badge/black]][repo/black]
[![Imports: isort][badge/isort]][isort]
[![pre-commit][badge/pre-commit]][repo/pre-commit]
[![Conventional Commits][badge/conventional-commits]][conventional-commits]

## Project Setup

Use pipenv to install packages. (e.g., `pipenv install <package>`)

```bash
pipenv --python 3.11 # Use python 3.11
pipenv shell # Activate virtual environment
pipenv install --dev # Install packages (`--dev` flag for development)

# Run `pre-commit` automatically on `git commit`
pre-commit install
pre-commit install --hook-type commit-msg
```

## How to Run

```bash
docker compose -f docker-compose.local.yml up -d
pipenv shell
make run
```

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

[badge/python-version]: https://img.shields.io/github/pipenv/locked/python-version/sparcs-kaist/new-ara-api/master
[badge/black]: https://img.shields.io/badge/code%20style-black-000000
[badge/isort]: https://img.shields.io/badge/%20imports-isort-%231674b1?labelColor=ef8336
[badge/pre-commit]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit
[badge/conventional-commits]: https://img.shields.io/badge/Conventional%20Commits-1.0.0-%23FE5196?logo=conventionalcommits&logoColor=white
[isort]: https://pycqa.github.io/isort
[conventional-commits]: https://conventionalcommits.org
[pep-484]: https://peps.python.org/pep-0484/
[repo/black]: https://github.com/psf/black
[repo/pre-commit]: https://github.com/pre-commit/pre-commit
