import os
import environ
from os import environ as os_environ

root = environ.Path(__file__) - 3

env = environ.Env(
    DJANGO_ENV=(str, 'development'),
    SECRET_KEY=(str, os_environ.get('SECRET_KEY', 'QWEFdgRefhtYTdrhEt43rt4398tgtrghTewg5iorjehinht')),
    AWS_BUCKET_NAME=(str, 'sparcs-kaist-ara-beta'),
    AWS_BUCKET_NAME_STATIC=(str, 'sparcs-kaist-ara-beta-static'),
    AWS_ACCESS_KEY_ID=(str, os_environ.get('AWS_ACCESS_KEY_ID')),
    AWS_SECRET_ACCESS_KEY=(str, os_environ.get('AWS_SECRET_ACCESS_KEY')),
    SSO_CLIENT_ID=(str, os_environ.get('SSO_CLIENT_ID')),
    SSO_SECRET_KEY=(str, os_environ.get('SSO_SECRET_KEY')),
    PORTAL_ID=(str, os_environ.get('PORTAL_ID')),
    PORTAL_PASSWORD=(str, os_environ.get('PORTAL_PASSWORD')),
)

# For local environment
if os.path.exists(root('.env')):
    environ.Env.read_env(env_file=root('.env'))
    env = environ.Env(
        SECRET_KEY=(str),
        AWS_BUCKET_NAME=(str),
        AWS_BUCKET_NAME_STATIC=(str),
        AWS_ACCESS_KEY_ID=(str),
        AWS_SECRET_ACCESS_KEY=(str),
        SSO_CLIENT_ID=(str),
        SSO_SECRET_KEY=(str)
    )
