import os

import firebase_admin
from firebase_admin import credentials

from ara.settings import BASE_DIR

cred_path = os.path.join(BASE_DIR, "firebaseServiceAccountKey.json")
cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)
