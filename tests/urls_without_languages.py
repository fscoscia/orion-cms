"""A root URLconf without per-language routes, as left by ``include("orion.urls")``."""

from django.urls import path

from orion.core.views import health_check

urlpatterns = [
    path("health/", health_check, name="health_check"),
]
