from os import environ as os_environ

import environ

root = environ.Path(__file__) - 3

env = environ.Env(
    DJANGO_ENV=(str, "development"),
    SECRET_KEY=(
        str,
        os_environ.get("SECRET_KEY", "QWEFdgRefhtYTdrhEt43rt4398tgtrghTewg5iorjehinht"),
    ),
    AWS_BUCKET_NAME=(str, os_environ.get("AWS_BUCKET_NAME", "sparcs-newara-dev")),
    AWS_BUCKET_NAME_STATIC=(
        str,
        os_environ.get("AWS_BUCKET_NAME_STATIC", "sparcs-kaist-ara-beta-static"),
    ),
    AWS_ACCESS_KEY_ID=(str, os_environ.get("AWS_ACCESS_KEY_ID")),
    AWS_SECRET_ACCESS_KEY=(str, os_environ.get("AWS_SECRET_ACCESS_KEY")),
    SSO_CLIENT_ID=(str, os_environ.get("SSO_CLIENT_ID")),
    SSO_SECRET_KEY=(str, os_environ.get("SSO_SECRET_KEY")),
    PORTAL_JSESSIONID=(str, os_environ.get("PORTAL_JSESSIONID")),
    HASH_SECRET_VALUE=(int, os_environ.get("HASH_SECRET_VALUE", "1")),
    ONE_APP_JWT_SECRET=(str, os_environ.get("ONE_APP_JWT_SECRET", "default_secret")),
)
