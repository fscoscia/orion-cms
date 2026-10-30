"""Validation for setting values that Django itself does not check."""

import re

from django.core.exceptions import ImproperlyConfigured

# Lowercase segments of letters, digits and hyphens, each followed by a slash.
ADMIN_PATH_PATTERN = re.compile(r"^(?:[a-z0-9-]+/)+$")


def validate_admin_path(admin_path: str) -> str:
    """Return ``admin_path`` if it is a valid relative URL path for the admin.

    The path is joined to the site root by Django's URL resolver, so it must not start
    with a slash and must end with one.
    """
    if not ADMIN_PATH_PATTERN.fullmatch(admin_path):
        raise ImproperlyConfigured(
            "ORION_ADMIN_PATH must be a relative path made of lowercase letters, "
            "digits and hyphens, without a leading slash and with a trailing slash "
            f"(for example 'admin/' or 'panel/'); got {admin_path!r}."
        )
    return admin_path
