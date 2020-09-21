import sys


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'console': {
            'level': 'INFO',
            'class': 'ara.log.handler.ConsoleHandler',
            'stream': sys.stdout
        },
        'rotating_file': {
            'level': 'INFO',
            'class': 'ara.log.handler.FileHandler',
            'filename': '/tmp/ara.log',
            'when': 'midnight',
            'backupCount': 10,
        }
    },
    'loggers': {
        'default': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'ara_logger': {
            'handlers': ['rotating_file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

LOG_ACCESS_FILE_PATH = '/var/log/newara/http_access.log'
LOG_ERROR_FILE_PATH = '/var/log/newara/http_error.log'
LOG_MAX_BYTE = 1024*1024*10
LOG_BACKUP_COUNT = 100