import logging

from django.conf import settings
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from orion.seo.meta import get_site
from orion.seo.models import NotFoundPath

logger = logging.getLogger(__name__)

MAX_PATH_LENGTH = NotFoundPath._meta.get_field("path").max_length


class NotFoundMiddleware:
    """Record the site paths that answer 404, for the admin's monitor."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404 and self._is_recorded(request):
            try:
                self._record(request)
            except DatabaseError:
                logger.exception("Could not record the 404 of %s", request.path)
        return response

    @staticmethod
    def _is_recorded(request):
        if request.method != "GET" or len(request.path) > MAX_PATH_LENGTH:
            return False
        ignored = (
            f"/{settings.ORION_ADMIN_PATH}",
            settings.STATIC_URL,
            settings.MEDIA_URL,
            "/_preview/",
        )
        return not request.path.startswith(
            tuple("/" + prefix.lstrip("/") for prefix in ignored if prefix)
        )

    @staticmethod
    def _record(request):
        site = get_site(request)
        if site is None:
            return
        paths = NotFoundPath.objects.filter(site=site, path=request.path)
        if paths.update(hits=F("hits") + 1, last_seen=timezone.now()):
            return
        if NotFoundPath.objects.count() >= settings.ORION_404_MAX_PATHS:
            return
        try:
            with transaction.atomic():
                NotFoundPath.objects.create(site=site, path=request.path)
        except IntegrityError:
            # Another request recorded it at the same time.
            paths.update(hits=F("hits") + 1)
