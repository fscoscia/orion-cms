"""What the Integrations screen and the admin home say about each integration."""

from urllib.parse import urlsplit

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

from orion.integrations.mail import EmailBackend
from orion.integrations.models import EmailStatus

OFF = "off"
UNTESTED = "untested"
ACTIVE = "active"
FAILING = "failing"

DJANGO_DEFAULT_FROM_EMAIL = "webmaster@localhost"


def get_email_problems():
    """What is missing from the SMTP settings, as messages."""
    problems = []
    if settings.EMAIL_HOST_USER and not settings.EMAIL_HOST_PASSWORD:
        problems.append(_("EMAIL_HOST_USER is set but EMAIL_HOST_PASSWORD is missing."))
    if settings.EMAIL_HOST_PASSWORD and not settings.EMAIL_HOST_USER:
        problems.append(_("EMAIL_HOST_PASSWORD is set but EMAIL_HOST_USER is missing."))
    if settings.DEFAULT_FROM_EMAIL == DJANGO_DEFAULT_FROM_EMAIL:
        problems.append(
            _("DEFAULT_FROM_EMAIL is missing: emails would leave from %(address)s.")
            % {"address": DJANGO_DEFAULT_FROM_EMAIL}
        )
    return problems


def is_tracked():
    """Whether the email backend records deliveries (the project may replace it)."""
    try:
        return issubclass(import_string(settings.EMAIL_BACKEND), EmailBackend)
    except ImportError:
        return False


def get_email_state():
    """The email's state, its configuration problems and the delivery record."""
    status = EmailStatus.load()
    problems = get_email_problems() if settings.EMAIL_HOST else []
    if not settings.EMAIL_HOST:
        state = OFF
    elif problems or status.is_failing:
        state = FAILING
    elif status.last_success_at is None:
        state = UNTESTED
    else:
        state = ACTIVE
    return {"state": state, "problems": problems, "status": status}


def get_email_settings():
    """The SMTP settings in use, without the password."""
    if settings.EMAIL_USE_SSL:
        security = "SSL"
    elif settings.EMAIL_USE_TLS:
        security = "TLS"
    else:
        security = _("None")
    return {
        "host": settings.EMAIL_HOST,
        "port": settings.EMAIL_PORT,
        "user": settings.EMAIL_HOST_USER,
        "has_password": bool(settings.EMAIL_HOST_PASSWORD),
        "security": security,
        "from_email": settings.DEFAULT_FROM_EMAIL,
        "timeout": settings.EMAIL_TIMEOUT,
        "backend": settings.EMAIL_BACKEND,
        "is_tracked": is_tracked(),
    }


def get_map_provider():
    """The host the map tiles come from, and whether it is OpenStreetMap's."""
    host = urlsplit(settings.ORION_MAP_TILES.get("url", "")).hostname or ""
    return {"host": host, "is_openstreetmap": host.endswith("openstreetmap.org")}
