"""Assign and validate the fields a caller sends for a model."""

import json

from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.fields.files import FieldFile
from wagtail.fields import RichTextField, StreamField

from orion.operations.richtext import clean_block_value, clean_rich_text

PAGE_TEXT_FIELDS = {"title", "slug", "seo_title", "search_description"}


def writable_page_fields(model):
    """The fields of a page type that a caller may write."""
    from wagtail.models import Page

    own = {field.name for field in Page._meta.get_fields()}
    extra = {
        field.name
        for field in model._meta.get_fields()
        if getattr(field, "concrete", False)
        and field.editable
        and not field.auto_created
        and field.name not in own
        and not field.primary_key
    }
    return PAGE_TEXT_FIELDS | extra


def writable_model_fields(model, exclude=()):
    return {
        field.name
        for field in model._meta.get_fields()
        if getattr(field, "concrete", False)
        and field.editable
        and not field.auto_created
        and not field.primary_key
        and field.name not in exclude
    }


def snapshot(instance, names):
    """The stored values of some fields, as plain data that JSON can keep."""
    return json.loads(
        json.dumps(
            {
                name: _plain(instance._meta.get_field(name).value_from_object(instance))
                for name in names
            },
            cls=DjangoJSONEncoder,
        )
    )


def _plain(value):
    return value.name if isinstance(value, FieldFile) else value


def changes(before, after):
    """What changed between two snapshots: the old and the new values, per field."""
    names = [name for name in after if before.get(name) != after[name]]
    return {
        "values": {name: before[name] for name in names},
        "after": {name: after[name] for name in names},
    }


def assign_fields(instance, values, allowed):
    """Set `values` on `instance`, cleaning and validating each one as the editor would.

    Unknown or internal fields are rejected, not ignored.
    """
    if not isinstance(values, dict):
        raise ValidationError("The fields must be an object.")
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ValidationError(
            f"These fields cannot be written: {', '.join(unknown)}. "
            f"Writable fields: {', '.join(sorted(allowed))}."
        )
    errors = {}
    for name, value in values.items():
        field = instance._meta.get_field(name)
        try:
            _assign(instance, field, value)
        except ValidationError as error:
            errors[name] = error.messages
    if errors:
        raise ValidationError(errors)


def _assign(instance, field, value):
    if isinstance(field, StreamField):
        value = _stream_value(field, value)
    elif isinstance(field, RichTextField):
        value = clean_rich_text(value, field.features)
    elif isinstance(field, models.ForeignKey):
        setattr(instance, field.attname, value)
        return
    else:
        value = field.to_python(value)
    setattr(instance, field.name, value)


def _stream_value(field, raw):
    if not isinstance(raw, list):
        raise ValidationError("A body must be a list of blocks.")
    cleaned = clean_block_value(field.stream_block, raw)
    try:
        value = field.to_python(cleaned)
        field.stream_block.clean(value)
    except ValidationError:
        raise
    except Exception as error:  # a malformed block can fail in many ways
        raise ValidationError("The body has a block that is not valid.") from error
    return value
