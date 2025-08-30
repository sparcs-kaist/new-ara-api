"""
ASGI entrypoint. Configures Django and then runs the application
defined in the ASGI_APPLICATION setting.
"""

import os
from ara.websocket import application as websocket_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ara.settings')

application = websocket_application