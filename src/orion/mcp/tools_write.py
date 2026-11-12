"""Tools that write drafts, redirects and site settings.

They only exist when the server was started with --allow-writes, and they act as the
technical account. All the rules (permissions, validation, revisions) live in
`orion.operations`; here the arguments come in and the failures go back as answers.
"""

import functools

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Page, get_page_models

from orion import operations
from orion.mcp.models import OperationReceipt
from orion.mcp.receipts import TRACKED_TOOLS
from orion.mcp.registry import (
    ACCESS_DRAFT,
    ACCESS_SETTINGS,
    OPERATION_KEY,
    ToolError,
    tool,
)
from orion.mcp.serialization import instance_data
from orion.operations.errors import RevisionConflictError
from orion.operations.fields import snapshot
from orion.site_data.models import SiteSettings, SiteTexts

NOT_PUBLISHED = (
    "It is saved as a draft: a person reviews and publishes it in the admin."
)
FIELDS = {
    "type": "object",
    "description": "Field names and their new values.",
}


def _explain(error):
    if hasattr(error, "error_dict"):
        return "; ".join(
            f"{field}: {' '.join(messages)}"
            for field, messages in error.message_dict.items()
        )
    return " ".join(error.messages)


def as_answer(function):
    """Turn the failures of an operation into a tool error with the cause."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except PermissionDenied as error:
            raise ToolError(f"Not allowed: {error}") from error
        except ValidationError as error:
            raise ToolError(f"Not valid: {_explain(error)}") from error
        except RevisionConflictError as error:
            raise ToolError(str(error)) from error
        except ObjectDoesNotExist as error:
            raise ToolError(f"Not found: {error}") from error

    return wrapper


def _page_result(page):
    return {
        "id": page.pk,
        "type": page._meta.label_lower,
        "title": page.title,
        "slug": page.slug,
        "live": page.live,
        "latest_revision_id": page.latest_revision_id,
        "note": NOT_PUBLISHED,
    }


def _page_type(label):
    for model in get_page_models():
        if model._meta.label_lower == label and not model._meta.abstract:
            return model
    raise ToolError(f"Unknown page type: {label}. Use the `schema` tool to list them.")


@tool(
    "page_create_draft",
    "Create a page as an unpublished draft under a parent page.",
    properties={
        "parent_id": {"type": "integer", "minimum": 1},
        "page_type": {
            "type": "string",
            "description": "For example orion_pages.contentpage (see `schema`).",
        },
        "fields": FIELDS,
    },
    required=["parent_id", "page_type", "fields"],
    access=ACCESS_DRAFT,
)
@as_answer
def page_create_draft(context, parent_id, page_type, fields):
    parent = Page.objects.get(pk=parent_id)
    page = operations.create_page_draft(
        context.actor, parent, _page_type(page_type), fields
    )
    return _page_result(page)


@tool(
    "page_update_draft",
    "Save new field values of a page as a new unpublished revision. Pass the "
    "`latest_revision_id` you read with `page_get`.",
    properties={
        "id": {"type": "integer", "minimum": 1},
        "expected_revision": {"type": "integer", "minimum": 1},
        "fields": FIELDS,
    },
    required=["id", "expected_revision", "fields"],
    access=ACCESS_DRAFT,
)
@as_answer
def page_update_draft(context, id, expected_revision, fields):
    page = operations.update_page_draft(
        context.actor, Page.objects.get(pk=id), fields, expected_revision
    )
    return _page_result(page)


REDIRECT_PROPERTIES = {
    "old_path": {"type": "string", "description": "The old path, e.g. /viejo."},
    "redirect_link": {
        "type": "string",
        "description": "An absolute http(s) URL. Use redirect_page for this site.",
    },
    "redirect_page": {"type": "integer", "minimum": 1},
    "is_permanent": {"type": "boolean"},
}


def _redirect_result(redirect):
    return {
        "id": redirect.pk,
        "old_path": redirect.old_path,
        "target_page_id": redirect.redirect_page_id,
        "target_link": redirect.redirect_link,
        "is_permanent": redirect.is_permanent,
    }


@tool(
    "redirect_create",
    "Create a redirect from an old path to a page or an absolute URL. Needs the "
    "permission to manage redirects, which Editors do not have.",
    properties=REDIRECT_PROPERTIES,
    required=["old_path"],
    access=ACCESS_SETTINGS,
)
@as_answer
def redirect_create(context, **values):
    redirect = operations.create_redirect(context.actor, values)
    context.undo["record"] = {"kind": "redirect_created"}
    return _redirect_result(redirect)


@tool(
    "redirect_update",
    "Change a redirect; the fields you leave out are kept.",
    properties={"id": {"type": "integer", "minimum": 1}, **REDIRECT_PROPERTIES},
    required=["id"],
    access=ACCESS_SETTINGS,
)
@as_answer
def redirect_update(context, id, **values):
    redirect = operations.update_redirect(
        context.actor, Redirect.objects.get(pk=id), values
    )
    context.undo["record"] = {"kind": "redirect", "id": id, **redirect.change}
    return _redirect_result(redirect)


@tool(
    "site_settings_update",
    "Update the site data (identity, contact, social networks, SEO). Needs the "
    "permission to change the site data, which Editors do not have.",
    properties={"fields": FIELDS},
    required=["fields"],
    access=ACCESS_SETTINGS,
)
@as_answer
def site_settings_update(context, fields):
    settings = operations.update_site_settings(context.actor, fields)
    context.undo["record"] = {"kind": "site_settings", **settings.change}
    return instance_data(settings, exclude={"id"})


@tool(
    "site_texts_update",
    "Update the site texts (tagline, description, legal text) of one language.",
    properties={
        "language": {"type": "string", "description": "A language code, e.g. es."},
        "fields": FIELDS,
    },
    required=["language", "fields"],
    access=ACCESS_SETTINGS,
)
@as_answer
def site_texts_update(context, language, fields):
    texts = operations.update_site_texts(context.actor, language, fields)
    context.undo["record"] = (
        {"kind": "site_texts", "language": language, **texts.change}
        if texts.change
        else {"kind": "site_texts_created"}
    )
    return {"language": language, **instance_data(texts, exclude={"id", "locale"})}


BY_HAND = (
    "It cannot be undone with a tool, because that would mean deleting something. "
    "Correct it by hand in the admin."
)


def _current(record):
    """The fields of the target as they are now, or None if it is gone."""
    from wagtail.models import Locale

    names = list(record["after"])
    if record["kind"] == "site_settings":
        target = SiteSettings.objects.first()
    elif record["kind"] == "site_texts":
        locale = Locale.objects.filter(language_code=record["language"]).first()
        target = SiteTexts.objects.filter(locale=locale).first()
    else:
        target = Redirect.objects.filter(pk=record["id"]).first()
    return None if target is None else (target, snapshot(target, names))


def _put_back(actor, record, target):
    values = record["values"]
    if record["kind"] == "site_settings":
        operations.update_site_settings(actor, values)
    elif record["kind"] == "site_texts":
        operations.update_site_texts(actor, record["language"], values)
    else:
        operations.update_redirect(actor, target, values)


@tool(
    "settings_revert",
    "Undo a write of redirects, site data or site texts, with the `operation_key` "
    "that the write returned. It only restores the fields if nobody changed them "
    "afterwards, and it cannot undo a redirect that was created.",
    properties={"reverts": {**OPERATION_KEY, "description": "The key to undo."}},
    required=["reverts"],
    access=ACCESS_SETTINGS,
    needs_key=True,
)
@as_answer
def settings_revert(context, reverts):
    if context.key is None:
        raise ToolError("Only an API key keeps receipts, so only it can undo a write.")
    with transaction.atomic():
        receipt = (
            OperationReceipt.objects.select_for_update()
            .filter(key=context.key, operation_key=reverts, tool__in=TRACKED_TOOLS)
            .first()
        )
        record = receipt.before if receipt else None
        if not record:
            raise ToolError(
                "This operation cannot be reverted: there is no record of it for "
                "this key (receipts are kept for 30 days)."
            )
        if receipt.reverted_at:
            return {"already_reverted": True, "operation_key": reverts}
        if record["kind"] in ("redirect_created", "site_texts_created"):
            raise ToolError(f"This operation created something. {BY_HAND}")
        found = _current(record)
        if found is None or found[1] != record["after"]:
            raise ToolError(
                "The values changed after that operation, so nothing was restored. "
                "Read them again and decide."
            )
        _put_back(context.actor, record, found[0])
        receipt.reverted_at = timezone.now()
        receipt.save(update_fields=["reverted_at"])
    return {"reverted": True, "operation_key": reverts, "restored": record["values"]}
