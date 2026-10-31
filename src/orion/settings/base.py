"""Base settings shared by every project built on Orion.

A project imports everything from this module and then adds what only it knows:
``ROOT_URLCONF``, ``WSGI_APPLICATION``, its own apps, and paths on disk such as
``STATIC_ROOT``, ``MEDIA_ROOT`` and template directories.

Every value that differs between environments, or that is secret, is read from
environment variables. See ``.env.example`` for the full list.
"""

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from orion.settings.env import env_bool, env_int, env_list, env_str
from orion.settings.validators import validate_admin_path

# Core

DEBUG = env_bool("DEBUG", default=False)

# Only used when DEBUG is on, so local development works without a .env file.
_DEVELOPMENT_SECRET_KEY = "django-insecure-orion-development-only"  # noqa: S105

SECRET_KEY = env_str("SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is false.")
    SECRET_KEY = _DEVELOPMENT_SECRET_KEY

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "[::1]"] if DEBUG else [],
)
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# Applications

ORION_APPS = [
    # Listed before Wagtail so Orion's templates take precedence over Wagtail's.
    "orion.core",
    "orion.localization",
    "orion.site_data",
    "orion.navigation",
    "orion.pages",
]

WAGTAIL_APPS = [
    "wagtail_localize",
    # Replaces wagtail.locales: same language screen, plus syncing new languages.
    "wagtail_localize.locales",
    "wagtail.contrib.settings",
    "wagtail.contrib.routable_page",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    "modelcluster",
    "taggit",
    "django_filters",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

INSTALLED_APPS = ORION_APPS + WAGTAIL_APPS + DJANGO_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # With i18n_patterns(prefix_default_language=False) the URL alone decides the
    # language: unprefixed URLs use LANGUAGE_CODE and the browser is ignored.
    "django.middleware.locale.LocaleMiddleware",
    "orion.localization.middleware.LocaleRedirectMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Exposes Wagtail settings to templates as settings.<app>.<Model>.
                "wagtail.contrib.settings.context_processors.settings",
            ],
        },
    },
]

# Database

DATABASE_URL = env_str("DATABASE_URL")
if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL must be set, for example postgres:///orion or "
        "mysql://user:password@host:3306/orion."
    )

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=env_int("DATABASE_CONN_MAX_AGE", 60),
        conn_health_checks=True,
    ),
}

if DATABASES["default"]["ENGINE"] == "django.db.backends.mysql":
    # Strict mode makes MySQL reject invalid data instead of truncating it silently.
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].setdefault(
        "init_command", "SET sql_mode='STRICT_TRANS_TABLES'"
    )

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation."
        "UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization

LANGUAGE_CODE = env_str("LANGUAGE_CODE", "es")
TIME_ZONE = env_str("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

# Catalog of languages a site can add from the admin. Names are written in each
# language so visitors recognise their own. Projects may replace the list; the base
# language must stay in it (check orion.E002).
LANGUAGES = [
    ("ar", "العربية"),
    ("ca", "Català"),
    ("cs", "Čeština"),
    ("da", "Dansk"),
    ("de", "Deutsch"),
    ("el", "Ελληνικά"),
    ("en", "English"),
    ("es", "Español"),
    ("eu", "Euskara"),
    ("fi", "Suomi"),
    ("fr", "Français"),
    ("gl", "Galego"),
    ("he", "עברית"),
    ("hi", "हिन्दी"),
    ("it", "Italiano"),
    ("ja", "日本語"),
    ("ko", "한국어"),
    ("nb", "Norsk bokmål"),
    ("nl", "Nederlands"),
    ("pl", "Polski"),
    ("pt", "Português"),
    ("ro", "Română"),
    ("ru", "Русский"),
    ("sv", "Svenska"),
    ("tr", "Türkçe"),
    ("uk", "Українська"),
    ("zh-hans", "简体中文"),
]
WAGTAIL_I18N_ENABLED = True
# Slugs in ASCII ("articulo", not "artículo"), so URLs read the same when shared.
WAGTAIL_ALLOW_UNICODE_SLUGS = False
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Maps. Tiles come from OpenStreetMap by default: its usage policy requires the
# attribution and does not allow heavy traffic. Projects may replace the whole dict.
ORION_MAP_TILES = {
    "url": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "attribution": (
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
        "contributors"
    ),
    "max_zoom": 19,
}
# Where the admin's location picker starts when no location is set: (lat, lng, zoom).
ORION_MAP_DEFAULT_CENTER = (-25.2637, -57.5759, 12)

# Static and media files (projects set STATIC_ROOT and MEDIA_ROOT)

STATIC_URL = "static/"
MEDIA_URL = "media/"

# Email

EMAIL_HOST = env_str("EMAIL_HOST")
EMAIL_PORT = env_int("EMAIL_PORT", 587)
EMAIL_HOST_USER = env_str("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env_str("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = env_bool("EMAIL_USE_SSL", default=False)
# Encrypted by default: TLS unless SSL was chosen, so credentials never travel in clear
# text just because a variable was left out.
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", default=not EMAIL_USE_SSL)
EMAIL_TIMEOUT = env_int("EMAIL_TIMEOUT", 10)
DEFAULT_FROM_EMAIL = env_str("DEFAULT_FROM_EMAIL", "webmaster@localhost")
SERVER_EMAIL = DEFAULT_FROM_EMAIL

if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
elif DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # Without SMTP in production, discard emails instead of writing messages that may
    # hold personal data to the server logs.
    EMAIL_BACKEND = "django.core.mail.backends.dummy.EmailBackend"

# Security

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
# Wagtail's live preview renders pages in an iframe on the same site.
X_FRAME_OPTIONS = "SAMEORIGIN"

# Wagtail

WAGTAIL_SITE_NAME = env_str("WAGTAIL_SITE_NAME", "Orion")
WAGTAILADMIN_BASE_URL = env_str("WAGTAILADMIN_BASE_URL", "http://localhost:8000")
WAGTAILSEARCH_BACKENDS = {
    "default": {"BACKEND": "wagtail.search.backends.database"},
}
# Page editors with many StreamField blocks exceed Django's default of 1000 fields.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# Orion

ORION_ADMIN_PATH = validate_admin_path(env_str("ORION_ADMIN_PATH", "admin/"))
