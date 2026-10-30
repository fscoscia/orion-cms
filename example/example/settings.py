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

# Compiling Orion's stylesheet (`pipenv run css-build`). The output goes into the
# package, so the compiled CSS ships with Orion; only this sandbox needs the tool.
ORION_PACKAGE_DIR = BASE_DIR.parent / "src" / "orion"
INSTALLED_APPS += ["django_tailwind_cli"]
STATICFILES_DIRS = [ORION_PACKAGE_DIR / "core" / "static"]
TAILWIND_CLI_VERSION = "4.3.3"
TAILWIND_CLI_SRC_CSS = ORION_PACKAGE_DIR / "core" / "static_src" / "orion.css"
TAILWIND_CLI_DIST_CSS = "orion/css/orion.css"
TAILWIND_CLI_PATH = BASE_DIR / ".tailwind"
