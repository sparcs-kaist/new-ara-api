from os import environ as os_environ


ELASTICSEARCH_DSL = {
    'default': {
        'hosts': f"{os_environ.get('ELASTICSEARCH_HOST', 'localhost')}:9200",
        'timeout': 30,
        'max_retries': 3,
        'retry_on_timeout': True,
    },
}
