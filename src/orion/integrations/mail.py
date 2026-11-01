"""An SMTP backend that records whether emails go out, for the Integrations screen."""

import logging

from django.core.mail.backends import smtp
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext

from orion.integrations.models import EmailStatus

logger = logging.getLogger(__name__)

ERROR_MAX_LENGTH = 500


def _record(**fields):
    # A database error must never stop an email, nor break the caller's transaction.
    try:
        with transaction.atomic():
            EmailStatus.objects.update_or_create(pk=1, defaults=fields)
    except Exception:
        logger.exception("Could not record the email status")


def record_success():
    _record(last_success_at=timezone.now())


def record_failure(error):
    """Record a failed delivery; ``error`` is an exception or a message."""
    if isinstance(error, Exception):
        error = f"{type(error).__name__}: {error}"
    _record(last_failure_at=timezone.now(), last_error=str(error)[:ERROR_MAX_LENGTH])


class EmailBackend(smtp.EmailBackend):
    """Django's SMTP backend, recording each delivery's outcome."""

    def open(self):
        # Wagtail opens the connection itself before sending its notifications.
        try:
            return super().open()
        except Exception as error:
            record_failure(error)
            error.orion_recorded = True
            raise

    def send_messages(self, email_messages):
        try:
            sent = super().send_messages(email_messages)
        except Exception as error:
            if not getattr(error, "orion_recorded", False):
                record_failure(error)
            raise
        expected = sum(1 for message in email_messages if message.recipients())
        if sent:
            record_success()
        if sent < expected:
            # With fail_silently the backend hides the error.
            record_failure(gettext("The mail server did not accept every message."))
        return sent
