"""What kind of site path a request is for, wherever the site is mounted.

Under a URL prefix (``SCRIPT_NAME``), ``request.path`` carries it and
``request.path_info`` does not. ``STATIC_URL`` and ``MEDIA_URL`` carry it as well, while
``ORION_ADMIN_PATH`` and the shared previews' path do not.
"""

from django.conf import settings

SHARED_PREVIEW_PATH = "/_preview/"


def is_admin_request(request):
    return request.path_info.startswith(f"/{settings.ORION_ADMIN_PATH}")


def is_asset_request(request):
    urls = (settings.STATIC_URL, settings.MEDIA_URL)
    return request.path.startswith(tuple("/" + url.lstrip("/") for url in urls if url))


def is_internal_request(request):
    """Whether it is for the admin, for files or for a shared preview: none of them
    are public pages."""
    return (
        is_admin_request(request)
        or is_asset_request(request)
        or request.path_info.startswith(SHARED_PREVIEW_PATH)
    )
