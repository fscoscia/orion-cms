"""Clean the rich text a caller sends, as the editor's own widget would.

Wagtail stores rich text as HTML and shows it as it is. The editor keeps it safe
because its widget only produces the features the field allows. A caller that skips the
widget could send anything, so the text goes through the same converter: what the field
does not allow (scripts, event handlers, styles, other tags) does not survive.
"""

from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.rich_text import features as feature_registry


def clean_rich_text(html, features=None):
    if not isinstance(html, str):
        raise ValidationError("A rich text must be a string.")
    converter = ContentstateConverter(
        features if features is not None else feature_registry.get_default_features()
    )
    try:
        return converter.to_database_format(converter.from_database_format(html))
    except Exception as error:  # the converter fails with assorted errors on bad HTML
        raise ValidationError("The rich text is not valid HTML.") from error


def clean_block_value(block, value):
    """Clean every rich text inside the raw (stored) value of a block."""
    if isinstance(block, blocks.RichTextBlock):
        return clean_rich_text(value, block.features)
    if isinstance(block, blocks.StructBlock) and isinstance(value, dict):
        return {
            name: clean_block_value(block.child_blocks[name], child)
            if name in block.child_blocks
            else child
            for name, child in value.items()
        }
    if isinstance(block, blocks.StreamBlock) and isinstance(value, list):
        return [_clean_stream_item(block, item) for item in value]
    if isinstance(block, blocks.ListBlock) and isinstance(value, list):
        return [_clean_list_item(block, item) for item in value]
    return value


def _clean_stream_item(block, item):
    kind = item.get("type") if isinstance(item, dict) else None
    if kind not in block.child_blocks:
        raise ValidationError(f"There is no block of type {kind!r}.")
    child = block.child_blocks[kind]
    return {**item, "value": clean_block_value(child, item.get("value"))}


def _clean_list_item(block, item):
    # Lists store {"type": "item", "value": ...}; older data stores the bare value.
    if isinstance(item, dict) and item.get("type") == "item" and "value" in item:
        return {**item, "value": clean_block_value(block.child_block, item["value"])}
    return clean_block_value(block.child_block, item)
