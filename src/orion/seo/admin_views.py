"""The admin's monitor of URLs that answer 404: administrators redirect or discard
them."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST
from wagtail.contrib.redirects.forms import RedirectForm

from orion.editor.roles import is_site_administrator
from orion.seo.models import NotFoundPath

PER_PAGE = 50


def _check_access(request):
    if not is_site_administrator(request.user):
        raise PermissionDenied


def index(request):
    _check_access(request)
    paths = NotFoundPath.objects.select_related("site").order_by("-hits", "path")
    return TemplateResponse(
        request,
        "orion/seo/not_found_index.html",
        {"paths": Paginator(paths, PER_PAGE).get_page(request.GET.get("p"))},
    )


@require_http_methods(["GET", "POST"])
def create_redirect(request, pk):
    _check_access(request)
    not_found = get_object_or_404(NotFoundPath, pk=pk)
    form = RedirectForm(
        request.POST or None,
        initial={"old_path": not_found.path, "site": not_found.site},
    )
    if form.is_valid():
        # Saving the redirect removes the path from the monitor (see signals).
        form.save()
        messages.success(
            request,
            _("%(path)s now redirects.") % {"path": not_found.path},
        )
        return redirect("orion_not_found_index")
    return TemplateResponse(
        request,
        "orion/seo/not_found_redirect.html",
        {"form": form, "not_found": not_found},
    )


@require_POST
def discard(request, pk):
    _check_access(request)
    NotFoundPath.objects.filter(pk=pk).delete()
    return redirect("orion_not_found_index")
