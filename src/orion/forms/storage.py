"""Private storage for form attachments: outside MEDIA_ROOT, so no URL serves them."""

from pathlib import Path

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def get_private_root():
    """ORION_FORMS_PRIVATE_ROOT, or a "private" folder next to MEDIA_ROOT."""
    if settings.ORION_FORMS_PRIVATE_ROOT:
        return Path(settings.ORION_FORMS_PRIVATE_ROOT).resolve()
    return Path(settings.MEDIA_ROOT).resolve().parent / "private"


def get_private_storage():
    # Built on each use: the root comes from settings that tests and projects change.
    return FileSystemStorage(location=get_private_root(), base_url=None)
