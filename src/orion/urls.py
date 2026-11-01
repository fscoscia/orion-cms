"""URL routes that Orion provides to every project.

Add these routes to the end of the project's ``ROOT_URLCONF`` instead of including the
module: Django only honours per-language routes at the top level of the root URLconf,
and Wagtail's page serving matches any path, so routes after it would never be reached::

    from orion.urls import urlpatterns as orion_urlpatterns

    urlpatterns = [...]  # the project's own routes
    urlpatterns += orion_urlpatterns
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail.documents import urls as wagtaildocs_urls

from orion.core.views import health_check
from orion.editor.preview_links import shared_preview
from orion.editor.views import admin_colors
from orion.search.views import SEARCH_PATH, search
from orion.seo.sitemap import Sitemap
from orion.seo.views import favicon, robots_txt

urlpatterns = [
    path("health/", health_check, name="health_check"),
    # Before the admin's routes: the login page needs it without a session.
    path(
        f"{settings.ORION_ADMIN_PATH}orion/colors.css",
        admin_colors,
        name="orion_admin_colors",
    ),
    path(settings.ORION_ADMIN_PATH, include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    # Before the pages, which match any path; the underscore keeps it off real slugs.
    path("_preview/<str:token>/", shared_preview, name="orion_shared_preview"),
    path("robots.txt", robots_txt, name="orion_robots_txt"),
    path("favicon.ico", favicon, name="orion_favicon"),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"pages": Sitemap}},
        name="orion_sitemap",
    ),
]

# Pages of the base language have no prefix; other languages use their code.
urlpatterns += i18n_patterns(
    # Before the pages, which match any path.
    path(SEARCH_PATH, search, name="orion_search"),
    path("", include(wagtail_urls)),
    prefix_default_language=False,
)
