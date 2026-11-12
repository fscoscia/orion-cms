"""Tools that report on the health and configuration of the site."""

from pathlib import Path

from django.conf import settings
from wagtail.contrib.redirects.models import Redirect

from orion.core.conventions import check_project
from orion.core.image_library import find_unused_images
from orion.core.views import database_is_reachable
from orion.forms.models import FormPage
from orion.mcp.registry import ACCESS_READ, paginate, tool
from orion.seo.models import NotFoundPath


@tool(
    "redirects_list",
    "The redirects of the site: old path, target and type.",
    paged=True,
    access=ACCESS_READ,
)
def redirects_list(**paging):
    redirects = Redirect.objects.select_related("redirect_page").order_by("old_path")
    return paginate(
        redirects,
        paging,
        lambda redirect: {
            "id": redirect.pk,
            "old_path": redirect.old_path,
            "target_page_id": redirect.redirect_page_id,
            "target_link": redirect.redirect_link,
            "is_permanent": redirect.is_permanent,
            "created_automatically": redirect.automatically_created,
        },
    )


@tool(
    "not_found_list",
    "The paths that answered 404, most visited first, to decide which need a redirect.",
    paged=True,
    access=ACCESS_READ,
)
def not_found_list(**paging):
    return paginate(
        NotFoundPath.objects.order_by("-hits", "-last_seen"),
        paging,
        lambda row: {
            "id": row.pk,
            "path": row.path,
            "hits": row.hits,
            "first_seen": row.first_seen,
            "last_seen": row.last_seen,
        },
    )


@tool(
    "forms_list",
    "The forms of the site with their fields and where the notice goes. It never "
    "includes what visitors sent.",
    paged=True,
    access=ACCESS_READ,
)
def forms_list(**paging):
    forms = FormPage.objects.prefetch_related("form_fields").order_by("path")
    return paginate(
        forms,
        paging,
        lambda form: {
            "id": form.pk,
            "title": form.title,
            "url": form.get_url(),
            "live": form.live,
            "notice_to": form.to_address,
            "notice_subject": form.subject,
            "fields": [
                {
                    "label": field.label,
                    "type": field.field_type,
                    "required": field.required,
                    "choices": field.choices,
                }
                for field in form.form_fields.all()
            ],
        },
    )


def _relative(path):
    try:
        return str(Path(path).relative_to(settings.BASE_DIR))
    except (AttributeError, ValueError):
        return str(path)


@tool(
    "conventions_check",
    "Hardcoded text in templates, images without alt text and incomplete "
    "translations, as `orion_check_conventions` reports them.",
    paged=True,
    access=ACCESS_READ,
)
def conventions_check(**paging):
    return paginate(
        check_project(),
        paging,
        lambda finding: {
            "path": _relative(finding.path),
            "line": finding.line,
            "message": finding.message,
        },
    )


@tool(
    "unused_images",
    "The images that no page, snippet or setting uses. Nothing is deleted.",
    paged=True,
    access=ACCESS_READ,
)
def unused_images(**paging):
    return paginate(
        find_unused_images(),
        paging,
        lambda image: {
            "id": image.pk,
            "title": image.title,
            "created_at": image.created_at,
            "size_bytes": image.get_file_size() or 0,
        },
    )


@tool("health", "Whether the application can reach its database.", access=ACCESS_READ)
def health():
    return {"status": "ok" if database_is_reachable() else "error"}
