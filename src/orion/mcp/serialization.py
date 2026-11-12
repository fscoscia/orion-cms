"""Turn model instances and blocks into plain data an assistant can read."""

from django.db.models.fields.files import FieldFile
from wagtail import blocks
from wagtail.fields import StreamField

MAX_BLOCK_DEPTH = 5


def field_value(instance, field):
    """The stored value of a field, as plain data."""
    value = field.value_from_object(instance)
    if isinstance(field, StreamField):
        return value.get_prep_value() if value is not None else []
    if isinstance(value, FieldFile):
        return value.name
    if value is None or isinstance(value, (bool, int, float, str, dict, list)):
        return value
    if hasattr(value, "isoformat"):
        return value  # dates and times; the JSON encoder writes them out
    return str(value)


def instance_data(instance, exclude=()):
    """The concrete fields of an instance by name; related objects as their id."""
    return {
        field.name: field_value(instance, field)
        for field in instance._meta.concrete_fields
        if field.name not in exclude
    }


def describe_block(block, name=None, depth=0):
    """A block with its type, label and, for nested blocks, its children."""
    info = {
        "name": name,
        "type": type(block).__name__,
        "label": str(block.label) if getattr(block, "label", None) else None,
        "required": block.required,
    }
    if depth >= MAX_BLOCK_DEPTH:
        return info
    if isinstance(block, (blocks.StructBlock, blocks.StreamBlock)):
        info["children"] = [
            describe_block(child, child_name, depth + 1)
            for child_name, child in block.child_blocks.items()
        ]
    elif isinstance(block, blocks.ListBlock):
        info["item"] = describe_block(block.child_block, None, depth + 1)
    elif isinstance(block, blocks.ChoiceBlock):
        info["choices"] = [
            str(value)
            for value, _label in block.field.choices
            if not isinstance(_label, (list, tuple))
        ]
    return info
