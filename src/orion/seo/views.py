from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from orion.seo.meta import get_site
from orion.site_data.models import SiteSettings

DEFAULT_ROBOTS_TXT = "User-agent: *\nDisallow: /{admin_path}\n"


@require_GET
def robots_txt(request):
    text = SiteSettings.load(request_or_site=request).robots_txt.strip()
    if not text:
        text = DEFAULT_ROBOTS_TXT.format(admin_path=settings.ORION_ADMIN_PATH)
    lines = text.replace("\r\n", "\n").rstrip("\n").split("\n")
    if not any(line.lower().startswith("sitemap:") for line in lines):
        site = get_site(request)
        root = site.root_url if site else request.build_absolute_uri("/").rstrip("/")
        lines.append(f"Sitemap: {root}{reverse('orion_sitemap')}")
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


@require_GET
def favicon(request):
    image = SiteSettings.load(request_or_site=request).favicon
    if image is None:
        raise Http404
    spec = "original|preserve-svg" if image.is_svg() else "fill-32x32|format-png"
    return HttpResponseRedirect(image.get_rendition(spec).url)
