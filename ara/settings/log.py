import sys


LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.server': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'default': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO'
        }
    }
}

LOG_ACCESS_FILE_PATH = '/var/log/newara/http_access.log'
LOG_ERROR_FILE_PATH = '/var/log/newara/http_error.log'
LOG_MAX_BYTE = 1024*1024*10
LOG_BACKUP_COUNT = 100