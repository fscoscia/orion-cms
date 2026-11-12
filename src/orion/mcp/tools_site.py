"""Tools that describe the site: its languages, settings, page types and pages."""

import django
import wagtail
from django.core.exceptions import ObjectDoesNotExist
from wagtail.models import Locale, Page, Site, get_page_models

from orion import __version__
from orion.localization.models import LanguageSettings
from orion.mcp.registry import ACCESS_READ, ToolError, paginate, tool
from orion.mcp.serialization import describe_block, field_value, instance_data
from orion.site_data.models import SiteSettings, SiteTexts

# Fields of a page that say nothing about its content or that point to accounts.
HIDDEN_PAGE_FIELDS = {
    "path",
    "depth",
    "numchild",
    "url_path",
    "content_type",
    "live_revision",
    "latest_revision",
    "owner",
    "locked",
    "locked_at",
    "locked_by",
    "alias_of",
}


@tool(
    "site_overview",
    "The site's name, languages (which are public) and versions.",
    access=ACCESS_READ,
)
def site_overview():
    site = Site.objects.filter(is_default_site=True).first()
    base = Locale.get_default()
    # Read the settings without `LanguageSettings.load()`, which creates a missing row.
    language_settings = LanguageSettings.objects.first()
    public = {base.pk}
    if language_settings is not None:
        public.update(language_settings.public_locales.values_list("pk", flat=True))
    return {
        "site_name": site.site_name if site else None,
        "hostname": site.hostname if site else None,
        "root_page_id": site.root_page_id if site else None,
        "base_language": base.language_code,
        "languages": [
            {
                "code": locale.language_code,
                "name": locale.get_display_name(),
                "is_base": locale.pk == base.pk,
                "is_public": locale.pk in public,
            }
            for locale in Locale.objects.order_by("language_code")
        ],
        "orion_version": __version__,
        "wagtail_version": wagtail.__version__,
        "django_version": django.get_version(),
    }


@tool(
    "site_settings",
    "The site data (identity, contact, social networks, SEO) and the site texts "
    "of each language.",
    access=ACCESS_READ,
)
def site_settings():
    site_settings = SiteSettings.objects.first()
    texts = [
        {
            "language": text.locale.language_code,
            **instance_data(text, exclude={"id", "locale"}),
        }
        for text in SiteTexts.objects.select_related("locale").order_by(
            "locale__language_code"
        )
    ]
    return {
        "site_data": instance_data(site_settings, exclude={"id", "site"})
        if site_settings
        else None,
        "site_texts": texts,
    }


def _stream_block_key(field):
    block_class = type(field.stream_block)
    return f"{block_class.__module__}.{block_class.__qualname__}"


def _page_type_models():
    return [
        model
        for model in get_page_models()
        if model is not Page and not model._meta.abstract
    ]


def _stream_fields(model):
    return [
        field for field in model._meta.get_fields() if hasattr(field, "stream_block")
    ]


@tool(
    "schema",
    "The page types of the site with their own fields and where each can be "
    "created, and the blocks of each body field (listed once under stream_blocks "
    "with name, type and label). Pass `block` with a block's name to get its "
    "fields in full.",
    properties={
        "block": {
            "type": "string",
            "description": "The name of a block, e.g. hero, to describe it in full.",
        }
    },
    access=ACCESS_READ,
)
def schema(block=None):
    if block is not None:
        return _describe_named_block(block)
    own_page_fields = {field.name for field in Page._meta.get_fields()}
    stream_blocks = {}
    page_types = []
    for model in _page_type_models():
        fields = []
        for field in model._meta.get_fields():
            if (
                not getattr(field, "concrete", False)
                or not field.editable
                or field.auto_created
                or field.name in own_page_fields
            ):
                continue
            info = {
                "name": field.name,
                "type": field.get_internal_type(),
                "required": not field.blank,
            }
            if field.related_model is not None:
                info["to"] = field.related_model._meta.label_lower
            if hasattr(field, "stream_block"):
                key = _stream_block_key(field)
                info["stream_block"] = key
                stream_blocks.setdefault(
                    key,
                    [
                        {
                            "name": name,
                            "type": type(child).__name__,
                            "label": str(child.label) if child.label else None,
                        }
                        for name, child in field.stream_block.child_blocks.items()
                    ],
                )
            fields.append(info)
        page_types.append(
            {
                "type": model._meta.label_lower,
                "name": str(model._meta.verbose_name),
                "parent_page_types": [
                    parent._meta.label_lower
                    for parent in model.allowed_parent_page_models()
                ],
                "subpage_types": [
                    child._meta.label_lower for child in model.allowed_subpage_models()
                ],
                "fields": fields,
            }
        )
    return {"page_types": page_types, "stream_blocks": stream_blocks}


def _describe_named_block(name):
    definitions = {}
    for model in _page_type_models():
        for field in _stream_fields(model):
            child = field.stream_block.child_blocks.get(name)
            if child is not None:
                definitions.setdefault(
                    _stream_block_key(field), describe_block(child, name)
                )
    if not definitions:
        raise ToolError(f"There is no block named {name}.")
    return {"block": name, "definitions": definitions}


@tool(
    "page_tree",
    "The pages of the site in tree order, with type, URL, publication state and "
    "language.",
    properties={
        "parent_id": {
            "type": "integer",
            "minimum": 1,
            "description": "Only the descendants of this page.",
        },
        "language": {"type": "string", "description": "A language code, e.g. es."},
        "live": {"type": "boolean", "description": "Only published or unpublished."},
    },
    paged=True,
    access=ACCESS_READ,
)
def page_tree(parent_id=None, language=None, live=None, **paging):
    if parent_id is not None:
        try:
            pages = Page.objects.get(pk=parent_id).get_descendants()
        except ObjectDoesNotExist:
            raise ToolError(f"There is no page with id {parent_id}.") from None
    else:
        pages = Page.objects.filter(depth__gt=1)
    if language is not None:
        pages = pages.filter(locale__language_code=language)
    if live is not None:
        pages = pages.filter(live=live)
    pages = pages.select_related("locale", "content_type").order_by("path")

    result = paginate(pages, paging, lambda page: page)
    parent_paths = {page.path[: -Page.steplen] for page in result["items"]}
    parent_ids = dict(
        Page.objects.filter(path__in=parent_paths).values_list("path", "id")
    )
    result["items"] = [
        {
            "id": page.pk,
            "title": page.title,
            "type": f"{page.content_type.app_label}.{page.content_type.model}",
            "url": page.get_url(),
            "live": page.live,
            "has_unpublished_changes": page.has_unpublished_changes,
            "language": page.locale.language_code,
            "depth": page.depth,
            "parent_id": parent_ids.get(page.path[: -Page.steplen]),
        }
        for page in result["items"]
    ]
    return result


@tool(
    "page_get",
    "One page with all its fields; the body as it is stored. It shows the latest "
    "saved version, which may be a draft that is not published yet.",
    properties={"id": {"type": "integer", "minimum": 1}},
    required=["id"],
    access=ACCESS_READ,
)
def page_get(id):
    try:
        page = Page.objects.get(pk=id).specific
    except ObjectDoesNotExist:
        raise ToolError(f"There is no page with id {id}.") from None
    latest = page.get_latest_revision_as_object()
    data = {
        field.name: field_value(latest, field)
        for field in latest._meta.concrete_fields
        if field.name not in HIDDEN_PAGE_FIELDS
    }
    data["type"] = page._meta.label_lower
    data["url"] = page.get_url()
    data["language"] = page.locale.language_code
    data["has_unpublished_changes"] = page.has_unpublished_changes
    data["latest_revision_id"] = page.latest_revision_id
    return data
