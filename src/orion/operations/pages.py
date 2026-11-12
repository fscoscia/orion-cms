"""Create and edit pages as drafts, through revisions."""

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils.text import slugify
from wagtail.models import Page

from orion.operations.errors import RevisionConflictError
from orion.operations.fields import assign_fields, writable_page_fields
from orion.operations.permissions import require_actor


def create_page_draft(actor, parent, model, fields):
    """Create a page of type `model` under `parent` as an unpublished draft."""
    require_actor(actor)
    parent = parent.specific
    if not parent.permissions_for_user(actor).can_add_subpage():
        raise PermissionDenied("You do not have permission to add pages here.")
    if model not in parent.specific_class.allowed_subpage_models():
        raise ValidationError(
            f"A {model._meta.label_lower} page cannot be created under "
            f"{parent._meta.label_lower}."
        )
    if "title" not in fields or not fields["title"]:
        raise ValidationError({"title": ["A page needs a title."]})
    fields = {**fields}
    fields.setdefault("slug", slugify(fields["title"]))

    page = model(live=False, owner=actor)
    assign_fields(page, fields, writable_page_fields(model))
    with transaction.atomic():
        # Validates, including the slug among siblings; Wagtail logs the creation
        # to the owner.
        parent.add_child(instance=page)
        page.save_revision(user=actor, log_action=False)
    return Page.objects.get(pk=page.pk).specific


def update_page_draft(actor, page, fields, expected_revision):
    """Save `fields` on the latest version of `page` as a new revision, unpublished."""
    require_actor(actor)
    with transaction.atomic():
        locked = Page.objects.select_for_update().get(pk=page.pk)
        page = locked.specific
        permissions = page.permissions_for_user(actor)
        if not permissions.can_edit():
            raise PermissionDenied("You do not have permission to edit this page.")
        if permissions.page_locked():
            raise PermissionDenied("This page is locked: unlock it in the admin first.")
        if page.latest_revision_id != expected_revision:
            raise RevisionConflictError(expected_revision, page.latest_revision_id)
        draft = page.get_latest_revision_as_object()
        assign_fields(draft, fields, writable_page_fields(type(page)))
        draft.save_revision(user=actor, log_action="wagtail.edit")
    return Page.objects.get(pk=page.pk).specific
