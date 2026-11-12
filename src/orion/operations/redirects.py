"""Create and edit redirects."""

from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, Site

from orion.operations.fields import snapshot
from orion.operations.permissions import require_perm

WRITABLE = {"old_path", "redirect_link", "redirect_page", "is_permanent"}


def _clean(redirect, values):
    unknown = sorted(set(values) - WRITABLE)
    if unknown:
        raise ValidationError(f"These fields cannot be written: {', '.join(unknown)}.")
    if "old_path" in values:
        redirect.old_path = Redirect.normalise_path(values["old_path"])
    if "is_permanent" in values:
        redirect.is_permanent = bool(values["is_permanent"])
    if "redirect_link" in values:
        redirect.redirect_link = values["redirect_link"] or ""
    if "redirect_page" in values:
        page_id = values["redirect_page"]
        redirect.redirect_page = Page.objects.filter(pk=page_id).first()
        if page_id and redirect.redirect_page is None:
            raise ValidationError({"redirect_page": [f"No page with id {page_id}."]})
    if bool(redirect.redirect_link) == bool(redirect.redirect_page_id):
        raise ValidationError("A redirect needs a page or a link, not both nor none.")
    if redirect.redirect_link:
        _check_link(redirect.redirect_link)
        if _points_to_this_site(redirect.redirect_link, redirect.old_path):
            raise ValidationError("A redirect cannot point to itself.")
    elif redirect.redirect_page.url_path and _page_path(redirect) == redirect.old_path:
        raise ValidationError("A redirect cannot point to itself.")
    taken = Redirect.objects.filter(old_path=redirect.old_path, site=redirect.site)
    if taken.exclude(pk=redirect.pk).exists():
        raise ValidationError({"old_path": ["There is already a redirect from here."]})
    redirect.full_clean()


def _check_link(link):
    parts = urlparse(link)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValidationError(
            {"redirect_link": ["The link must be an http or https URL."]}
        )


def _points_to_this_site(link, old_path):
    """Whether a link leads back to the path being redirected, on one of the sites."""
    host = urlparse(link).hostname
    return (
        Site.objects.filter(hostname=host).exists()
        and Redirect.normalise_path(link) == old_path
    )


def _page_path(redirect):
    url = redirect.redirect_page.get_url()
    return Redirect.normalise_path(url) if url else None


def create_redirect(actor, values):
    require_perm(actor, "wagtailredirects.add_redirect", "create redirects")
    redirect = Redirect(is_permanent=True)
    _clean(redirect, {"is_permanent": True, **values})
    redirect.save()
    redirect.change = None  # undoing a created redirect would mean deleting it
    return redirect


REDIRECT_FIELDS = ["old_path", "redirect_link", "redirect_page", "is_permanent"]


def update_redirect(actor, redirect, values):
    require_perm(actor, "wagtailredirects.change_redirect", "change redirects")
    before = snapshot(redirect, REDIRECT_FIELDS)
    _clean(redirect, values)
    redirect.save()
    # All four fields travel together, so that going back from a link to a page works.
    redirect.change = {
        "values": before,
        "after": snapshot(redirect, REDIRECT_FIELDS),
    }
    return redirect
