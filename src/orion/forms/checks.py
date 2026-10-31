from pathlib import Path

from django.conf import settings
from django.core.checks import Error, Tags, register

from orion.forms.storage import get_private_root

PRIVATE_ROOT_ERROR_ID = "orion.E005"


@register(Tags.security)
def check_private_root(app_configs, **kwargs):
    """Form attachments must not be reachable through the public media URL."""
    if not settings.MEDIA_ROOT:
        return []
    media_root = Path(settings.MEDIA_ROOT).resolve()
    private_root = get_private_root()
    if private_root == media_root or media_root in private_root.parents:
        return [
            Error(
                "ORION_FORMS_PRIVATE_ROOT is inside MEDIA_ROOT, so form attachments "
                "would be public.",
                hint="Use a folder outside MEDIA_ROOT.",
                id=PRIVATE_ROOT_ERROR_ID,
            )
        ]
    return []
