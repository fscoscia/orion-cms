"""Shareable previews: temporary links that show a page's latest draft without an
account, and the admin screen where editors create and revoke them."""

from datetime import timedelta

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_http_methods
from wagtail.models import Page

from orion.editor.models import PreviewLink

DEFAULT_DAYS = 7


class PreviewLinkForm(forms.Form):
    days = forms.TypedChoiceField(
        label=_("Expires in"),
        choices=[
            (1, _("1 day")),
            (DEFAULT_DAYS, _("7 days")),
            (30, _("30 days")),
        ],
        coerce=int,
        initial=DEFAULT_DAYS,
    )


def can_share(user, page):
    return page.permissions_for_user(user).can_edit()


def link_url(request, link):
    # The admin and the site share the domain, so the link uses the admin's.
    return request.build_absolute_uri(
        reverse("orion_shared_preview", args=[link.token])
    )


@require_GET
def shared_preview(request, token):
    link = (
        PreviewLink.objects.active().filter(token=token).select_related("page").first()
    )
    if link is None:
        raise Http404
    page = link.page.specific.get_latest_revision_as_object()
    response = page.make_preview_request(request, page.default_preview_mode)
    response["X-Robots-Tag"] = "noindex, nofollow"
    response["Cache-Control"] = "private, no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


@require_http_methods(["GET", "POST"])
def manage(request, page_id):
    """List, create and revoke the preview links of a page."""
    page = get_object_or_404(Page, pk=page_id).specific
    if not can_share(request.user, page):
        raise PermissionDenied
    form = PreviewLinkForm(request.POST or None)
    if request.method == "POST":
        revoke = request.POST.get("revoke")
        if revoke:
            PreviewLink.objects.filter(page=page, pk=revoke).delete()
            messages.success(request, _("The link was revoked."))
            return redirect("orion_preview_links", page_id=page.pk)
        if form.is_valid():
            PreviewLink.objects.create(
                page=page,
                created_by=request.user,
                expires_at=timezone.now() + timedelta(days=form.cleaned_data["days"]),
            )
            messages.success(request, _("The link is ready to copy."))
            return redirect("orion_preview_links", page_id=page.pk)
    links = [
        {"link": link, "url": link_url(request, link)}
        for link in PreviewLink.objects.active()
        .filter(page=page)
        .select_related("created_by")
    ]
    return TemplateResponse(
        request,
        "orion/editor/preview_links.html",
        {"page": page, "form": form, "links": links},
    )
