import sys
import os

LOG_FILE_PATH = os.environ.get('LOG_FILE_PATH', '/var/log/newara/http_access.log')
LOG_MAX_BYTES = int(os.environ.get('LOG_MAX_BYTES', 1024 * 1024 * 10))
LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 100))

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
            'class': 'ara.log.handler.SizedTimedRotatingFileHandler',
            'filename': LOG_FILE_PATH,
            'max_bytes': LOG_MAX_BYTES,
            'backup_count': LOG_BACKUP_COUNT,
            'when': 'midnight',
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
