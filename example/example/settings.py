"""Settings for Orion's example project, used to develop and test the package.

This project is a local sandbox and must never be deployed. Client projects follow the
same pattern: set paths and project-specific values after importing Orion's base.
"""

import os
from pathlib import Path

# Local defaults so the sandbox runs without a .env file; variables already in the
# environment take precedence (under `pipenv run`, that includes the ones from .env).
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("DATABASE_URL", "postgres:///orion")

from orion.settings.base import *

BASE_DIR = Path(__file__).resolve().parent.parent

ROOT_URLCONF = "example.urls"
WSGI_APPLICATION = "example.wsgi.application"

STATIC_ROOT = BASE_DIR / "static"
MEDIA_ROOT = BASE_DIR / "media"
