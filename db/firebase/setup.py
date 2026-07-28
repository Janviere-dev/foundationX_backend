#!/usr/bin/env python3

import logging
import firebase_admin
from firebase_admin import credentials
from pathlib import Path
from core.config import get_settings

logger = logging.getLogger(__name__)

path_to_json = Path(get_settings().PATH_TO_FIREBASE)

def init_firebase():
    """
    initialize firebase
    """
    if not firebase_admin._apps:
        logger.info("Connecting to Firebase...")
        firebase_credential = credentials.Certificate(path_to_json)
        firebase_admin.initialize_app(firebase_credential)
        logger.info("Firebase connection established")
    else:
        logger.info("Firebase already initialized, skipping")
