"""System checks for setting combinations that Django only reports at send time."""

from django.conf import settings
from django.core.checks import Error, Tags, register

EMAIL_SSL_AND_TLS_ERROR_ID = "orion.E001"


@register(Tags.compatibility)
def check_email_security(app_configs, **kwargs):
    """Report enabling SSL and TLS together, which Django's SMTP backend rejects."""
    if settings.EMAIL_USE_SSL and settings.EMAIL_USE_TLS:
        return [
            Error(
                "EMAIL_USE_SSL and EMAIL_USE_TLS are both enabled.",
                hint=(
                    "Enable only one: SSL (usually port 465) or TLS (usually port 587)."
                ),
                id=EMAIL_SSL_AND_TLS_ERROR_ID,
            )
        ]
    return []
