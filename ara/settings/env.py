import environ


root = environ.Path(__file__) - 3

environ.Env.read_env(env_file=root('.env'))
env = environ.Env(
    DJANGO_ENV=(str, 'development'),
    SECRET_KEY=(str),
    DATABASE_URL=(str),
    AWS_BUCKET_NAME=(str),
    AWS_BUCKET_NAME_STATIC=(str),
    AWS_ACCESS_KEY_ID=(str),
    AWS_SECRET_ACCESS_KEY=(str),
    SSO_CLIENT_ID=(str),
    SSO_SECRET_KEY=(str)
)
