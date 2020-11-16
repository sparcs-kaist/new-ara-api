from os import environ as os_environ


ELASTICSEARCH_HOST = os_environ.get('NEWARA_ELASTICSEARCH_HOST', 'localhost')
ELASTICSEARCH_PORT = os_environ.get('NEWARA_ELASTICSEARCH_PORT', '9200')
ELASTICSEARCH_URL = os_environ.get('NEWARA_ELASTICSEARCH_URL', f'{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}')

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ELASTICSEARCH_URL,
        'timeout': 30,
        'max_retries': 3,
        'retry_on_timeout': True,
    },
}
