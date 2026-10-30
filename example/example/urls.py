from django.conf import settings

from orion.urls import urlpatterns as orion_urlpatterns

urlpatterns = []

if settings.DEBUG:
    from django.conf.urls.static import static

    # Django serves uploaded files only in development; production uses the web server.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Orion's routes go last because Wagtail's page serving matches any path. They are
# added rather than included because Django requires per-language routes at the top
# level of the root URLconf.
urlpatterns += orion_urlpatterns
