import logging

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe

logger = logging.getLogger(__name__)


@never_cache
@require_safe
def health_check(request):
    """Report whether the application can reach its database.

    The response never includes error details, so the endpoint can be public.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError:
        logger.exception("Health check failed: the database is not reachable.")
        return JsonResponse({"status": "error"}, status=503)
    return JsonResponse({"status": "ok"})
