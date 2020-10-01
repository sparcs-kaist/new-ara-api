from os import environ as os_environ


ELASTICSEARCH_HOST = os_environ.get('NEWARA_ELASTICSEARCH_HOST', 'localhost')

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': f'{ELASTICSEARCH_HOST}:9200',
        'timeout': 30,
        'max_retries': 3,
        'retry_on_timeout': True,
    },
}
