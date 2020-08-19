from .env import env


# https://github.com/etianen/django-s3-storage/

AWS_REGION = 'ap-northeast-2'

AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')

AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')

AWS_S3_BUCKET_AUTH = False

AWS_S3_MAX_AGE_SECONDS = 60 * 60 * 24 * 365

AWS_S3_BUCKET_NAME = env('AWS_BUCKET_NAME')

AWS_S3_BUCKET_NAME_STATIC = env('AWS_BUCKET_NAME_STATIC')


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

DEFAULT_FILE_STORAGE = 'django_s3_storage.storage.S3Storage'

STATICFILES_STORAGE = 'django_s3_storage.storage.StaticS3Storage'

AWS_SES_REGION_NAME = 'ap-northeast-2'

AWS_SES_REGION_ENDPOINT = 'email.ap-northeast-2.amazonaws.com'
