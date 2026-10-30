from django.conf import settings
from django.urls import include, path

urlpatterns = []

if settings.DEBUG:
    from django.conf.urls.static import static

    # Django serves uploaded files only in development; production uses the web server.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Orion's routes go last because Wagtail's page serving matches any path.
urlpatterns += [
    path("", include("orion.urls")),
]
