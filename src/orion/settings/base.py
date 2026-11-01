"""Base settings shared by every project built on Orion.

A project imports everything from this module and then adds what only it knows:
``ROOT_URLCONF``, ``WSGI_APPLICATION``, its own apps, and paths on disk such as
``STATIC_ROOT``, ``MEDIA_ROOT`` and template directories.

Every value that differs between environments, or that is secret, is read from
environment variables. See ``.env.example`` for the full list.
"""

from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from orion.settings.cache import parse_cache_url
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
    "orion.seo",
    "orion.forms",
    "orion.search",
    "orion.snippets",
    "orion.integrations",
    "orion.editor",
]

WAGTAIL_APPS = [
    "wagtail_localize",
    # Replaces wagtail.locales: same language screen, plus syncing new languages.
    "wagtail_localize.locales",
    "wagtail.contrib.settings",
    "wagtail.contrib.routable_page",
    "wagtail.contrib.redirects",
    "wagtail.contrib.forms",
    "wagtail.contrib.search_promotions",
    "wagtail.contrib.sitemaps",
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
    # Second factor for the admin: authenticator apps and backup codes.
    "django_otp",
    "django_otp.plugins.otp_totp",
    "django_otp.plugins.otp_static",
]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
]

INSTALLED_APPS = ORION_APPS + WAGTAIL_APPS + DJANGO_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # Visits served from the page cache skip everything below.
    "orion.core.cache.middleware.PageCacheMiddleware",
    # ETag on every page, and 304 when the browser already has it.
    "django.middleware.http.ConditionalGetMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # With i18n_patterns(prefix_default_language=False) the URL alone decides the
    # language: unprefixed URLs use LANGUAGE_CODE and the browser is ignored.
    "django.middleware.locale.LocaleMiddleware",
    "orion.localization.middleware.LocaleRedirectMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Requires the second factor on admin pages (ORION_2FA_REQUIRED).
    "orion.editor.middleware.TwoFactorMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Before the redirects: it sees the response after them, so only real 404s count.
    "orion.seo.middleware.NotFoundMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
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

# Cache: files by default, Redis or memory through CACHE_URL.

CACHES = {"default": parse_cache_url(env_str("CACHE_URL"), SECRET_KEY)}

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
# Spanish for the admin phrases Wagtail leaves untranslated. Highest priority, so it
# also reaches the admin's JavaScript catalog; projects add their own with +=.
LOCALE_PATHS = [Path(__file__).resolve().parent.parent / "editor" / "wagtail_locale"]
WAGTAIL_I18N_ENABLED = True
# Slugs in ASCII ("articulo", not "artículo"), so URLs read the same when shared.
WAGTAIL_ALLOW_UNICODE_SLUGS = False
WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

# Every admin user signs in with a second factor (authenticator app or backup code).
# Turn it off only for local development (check orion.W002).
ORION_2FA_REQUIRED = env_bool("ORION_2FA_REQUIRED", True)

# Wagtail's login form with translated labels.
WAGTAILADMIN_USER_LOGIN_FORM = "orion.editor.forms.LoginForm"

# No check for new Wagtail versions: the admin makes no external requests.
WAGTAIL_ENABLE_UPDATE_CHECK = False

# Admin colors, as hex: {"primary": "#...", "secondary": "#..."}. Empty keeps
# Wagtail's colors. The admin shows white text on them (checks orion.E004 and W001).
ORION_ADMIN_COLORS = {}

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

# Images: formats and weight accepted by the library, originals reduced to
# ORION_IMAGE_MAX_DIMENSION px, and renditions generated after each upload.
WAGTAILIMAGES_EXTENSIONS = ["avif", "gif", "jpg", "jpeg", "png", "svg", "webp"]
WAGTAILIMAGES_MAX_UPLOAD_SIZE = env_int("ORION_IMAGE_MAX_UPLOAD_MB", 10) * 1024 * 1024
WAGTAILIMAGES_IMAGE_FORM_BASE = "orion.core.image_forms.ImageForm"
ORION_IMAGE_MAX_DIMENSION = 2048
ORION_IMAGE_RENDITIONS_IN_BACKGROUND = True
# Projects add or replace named image sizes here (see orion.core.images).
ORION_IMAGE_SIZES = {}

# Full-page cache for visitors without a session (orion.core.cache). Projects add
# models shown on their pages ("app_label.Model") so that saving them empties it.
ORION_PAGE_CACHE = env_bool("ORION_PAGE_CACHE", not DEBUG)
ORION_PAGE_CACHE_SECONDS = 60 * 60 * 24
ORION_PAGE_CACHE_MODELS = []

# Forms (orion.forms). Attachments go to ORION_FORMS_PRIVATE_ROOT, never under
# MEDIA_ROOT; empty means a "private" folder next to MEDIA_ROOT.
ORION_FORMS_PRIVATE_ROOT = env_str("ORION_FORMS_PRIVATE_ROOT")
ORION_FORMS_UPLOAD_EXTENSIONS = ["pdf", "doc", "docx", "odt", "jpg", "jpeg", "png"]
ORION_FORMS_UPLOAD_MAX_MB = 5
ORION_FORMS_MIN_SECONDS = 3
# Submissions per visitor address and form: (count, seconds).
ORION_FORMS_RATE_LIMIT = (5, 600)
# None allows every field type; projects can list the ones editors may use.
ORION_FORMS_FIELD_TYPES = None
ORION_FORMS_MAX_FIELDS = 30
# Submissions and their files are deleted after this many months by
# `manage.py orion_purge_submissions` (daily cron); 0 keeps them.
ORION_FORMS_RETENTION_MONTHS = env_int("ORION_FORMS_RETENTION_MONTHS", 12)
# Email notices that could not go out are sent again by
# `manage.py orion_retry_form_emails` (cron) for this many days.
ORION_FORMS_EMAIL_RETRY_DAYS = env_int("ORION_FORMS_EMAIL_RETRY_DAYS", 3)

# Distinct paths that answered 404 kept for the admin's monitor.
ORION_404_MAX_PATHS = 1000

# Static and media files (projects set STATIC_ROOT and MEDIA_ROOT)

STATIC_URL = "static/"
MEDIA_URL = "media/"

# WhiteNoise serves static files compressed (Brotli and gzip), with hashed names and a
# one-year immutable cache. Outside DEBUG run collectstatic; in DEBUG files are served
# as they are.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
# A file missing from the manifest falls back to its plain name instead of failing.
WHITENOISE_MANIFEST_STRICT = False

# Static paths of the project's own woff2 fonts, preloaded on every page.
ORION_FONT_PRELOAD = []

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
    # Django's SMTP backend, recording each delivery for the admin's Integrations.
    EMAIL_BACKEND = "orion.integrations.mail.EmailBackend"
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
# The name authenticator apps show for the admin's second factor.
OTP_TOTP_ISSUER = WAGTAIL_SITE_NAME
WAGTAILADMIN_BASE_URL = env_str("WAGTAILADMIN_BASE_URL", "http://localhost:8000")
# PostgreSQL's text search configuration of each base language: plurals and variants
# match ("médicos" finds "médico"). MySQL and SQLite ignore it.
POSTGRES_SEARCH_CONFIGS = {
    "es": "spanish",
    "en": "english",
    "pt": "portuguese",
    "fr": "french",
    "it": "italian",
    "de": "german",
}
ORION_SEARCH_CONFIG = env_str(
    "ORION_SEARCH_CONFIG",
    POSTGRES_SEARCH_CONFIGS.get(LANGUAGE_CODE.split("-")[0], "simple"),
)
WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": "wagtail.search.backends.database",
        "SEARCH_CONFIG": ORION_SEARCH_CONFIG,
    },
}
# The site search (orion.search): the form in the header, and the distinct queries
# without results kept for the admin's report.
ORION_SEARCH_IN_HEADER = True
ORION_SEARCH_MAX_NO_RESULTS = 1000

# Emergency switch: true stops loading every code snippet (orion.snippets), for when one
# breaks the site and the admin cannot be used.
ORION_SCRIPTS_DISABLED = env_bool("ORION_SCRIPTS_DISABLED", False)
# Page editors with many StreamField blocks exceed Django's default of 1000 fields.
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000

# Orion

ORION_ADMIN_PATH = validate_admin_path(env_str("ORION_ADMIN_PATH", "admin/"))
