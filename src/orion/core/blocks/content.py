"""Content blocks that editors use to build pages.

Block keys and field names are a StreamField contract: renaming or removing one once
there is content requires a data migration.
"""

import datetime
import functools
import json
import re
import uuid
from types import SimpleNamespace

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.module_loading import import_string
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.telepath import register
from wagtail.admin.telepath.widgets import WidgetAdapter
from wagtail.blocks.struct_block import BlockGroup
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageBlock, ImageChooserBlock

from orion.core.blocks.links import AnchorBlock, LinkBlock
from orion.core.forms import LocationField
from orion.core.uploads import VIDEO_EXTENSIONS

DEFAULT_STYLE = "default"
RICH_TEXT_FEATURES = ["h2", "h3", "bold", "italic", "link", "ol", "ul"]
PARAGRAPH_PATTERN = re.compile(r"<p[\s>]")
# Ids of Orion's own templates, which a block's anchor would duplicate.
RESERVED_ANCHORS = {"main-content", "site-nav-panel"}


SAMPLE_IMAGE_SIZES = {
    "landscape-1.webp": (1600, 900),
    "landscape-2.webp": (1600, 900),
    "landscape-3.webp": (800, 800),
    "logo-1.svg": (200, 48),
    "logo-2.svg": (200, 48),
    "logo-3.svg": (200, 48),
    "logo-4.svg": (200, 48),
}


class SampleImage:
    """A sample image from Orion's static files, for block previews in the editor.

    Previews must work on an empty site without adding images to its library, so
    templates draw these with a plain <img> instead of renditions.
    """

    is_sample = True

    def __init__(self, name, alt=""):
        self.url = static(f"orion/samples/{name}")
        self.width, self.height = SAMPLE_IMAGE_SIZES[name]
        self.contextual_alt_text = alt
        self.decorative = not alt


def with_sample_images(value, **images):
    """Put sample images in a preview value.

    Pass a file name for an image field, or a list of names for a list whose items
    have an ``image`` field.
    """
    for field, names in images.items():
        if isinstance(names, list):
            for item, name in zip(value[field], names, strict=False):
                item["image"] = SampleImage(name, alt="Sample image")
        else:
            value[field] = SampleImage(names, alt="Sample image")
    return value


def get_block_style_choices(block_type):
    """Return the styles a project declares for ``block_type`` in ORION_BLOCK_STYLES.

    The default style always comes first, so a project without styles gets one option.
    """
    project_styles = getattr(settings, "ORION_BLOCK_STYLES", {}).get(block_type, [])
    return [(DEFAULT_STYLE, _("Standard"))] + [
        (key, label) for key, label in project_styles if key != DEFAULT_STYLE
    ]


class BlockStyleSelect(forms.Select):
    """A select that becomes a hidden input when there is only one style to choose."""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if len(list(self.choices)) <= 1:
            context["widget"]["type"] = "hidden"
            context["widget"]["value"] = value or DEFAULT_STYLE
            self.template_name = "django/forms/widgets/hidden.html"
        else:
            self.template_name = forms.Select.template_name
        return context


# The editor's Select adapter expects a <select>; the generic one handles both forms.
register(WidgetAdapter(), BlockStyleSelect)


class BlockStyleChoiceBlock(blocks.ChoiceBlock):
    """The "Style" field of content blocks, with choices read from the settings.

    The choices are a callable, so migrations keep a reference to it instead of the
    list and changing ORION_BLOCK_STYLES does not need a migration.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", BlockStyleSelect())
        super().__init__(*args, **kwargs)

    class Meta:
        form_classname = "orion-block-style"


class BaseContentBlock(blocks.StructBlock):
    """Base of Orion's content blocks: adds the "Anchor", "Style" and "Visible" fields.

    They go last and, in the editor, in the block's collapsible settings area.
    Subclasses set ``style_key``, the key projects use in ORION_BLOCK_STYLES.
    """

    style_key = None
    settings_block_names = ("anchor", "style", "is_visible")

    def __init__(self, local_blocks=None, **kwargs):
        style_block = BlockStyleChoiceBlock(
            choices=functools.partial(get_block_style_choices, self.style_key),
            default=DEFAULT_STYLE,
            label=_("Style"),
        )
        visible_block = blocks.BooleanBlock(
            default=True,
            required=False,
            label=_("Visible"),
            help_text=_("Turn off to hide the block without deleting it."),
        )
        anchor_block = AnchorBlock(
            label=_("Anchor"),
            help_text=_("Identifies the block so that links can point to it."),
        )
        # Passed to the constructor, which builds the editor's form layout.
        super().__init__(
            [
                *(local_blocks or []),
                ("anchor", anchor_block),
                ("style", style_block),
                ("is_visible", visible_block),
            ],
            **kwargs,
        )

    def get_form_layout(self):
        if self.meta.form_layout is not None:
            return super().get_form_layout()
        return BlockGroup(
            children=[
                name
                for name in self.child_blocks
                if name not in self.settings_block_names
            ],
            settings=list(self.settings_block_names),
        )

    def _with_valid_style(self, value):
        # A style removed from the settings falls back to the default one.
        valid_styles = {key for key, _label in get_block_style_choices(self.style_key)}
        if value.get("style") not in valid_styles:
            value["style"] = DEFAULT_STYLE
        return value

    def to_python(self, value):
        return self._with_valid_style(super().to_python(value))

    def bulk_to_python(self, values):
        return [
            self._with_valid_style(value) for value in super().bulk_to_python(values)
        ]


class EyebrowBlock(blocks.CharBlock):
    """A short text above a block's title."""

    def __init__(self, **kwargs):
        kwargs.setdefault("label", _("Eyebrow"))
        kwargs.setdefault("required", False)
        kwargs.setdefault("max_length", 80)
        kwargs.setdefault("help_text", _("A short text above the title."))
        super().__init__(**kwargs)


class HighlightedTitleBlock(blocks.RichTextBlock):
    """A one-paragraph title where bold words are highlighted with the accent color."""

    def __init__(self, required=True, **kwargs):
        kwargs.setdefault("label", _("Title"))
        kwargs.setdefault("help_text", _("Make words bold to highlight them."))
        super().__init__(features=["bold"], required=required, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        if len(PARAGRAPH_PATTERN.findall(value.source)) > 1:
            raise ValidationError(_("A title must be a single paragraph."))
        return value


class RichTextBodyBlock(blocks.RichTextBlock):
    """Body text limited to editorial formats."""

    def __init__(self, **kwargs):
        kwargs.setdefault("label", _("Text"))
        super().__init__(features=RICH_TEXT_FEATURES, **kwargs)


class ButtonBlock(LinkBlock):
    """A link shown as a button."""

    variant = blocks.ChoiceBlock(
        label=_("Button style"),
        choices=[("primary", _("Primary")), ("secondary", _("Secondary"))],
        default="primary",
    )

    class Meta:
        icon = "link"
        label = _("Button")


def button_list(min_num=0, max_num=2):
    return blocks.ListBlock(
        ButtonBlock(),
        label=_("Buttons"),
        min_num=min_num,
        max_num=max_num,
        default=[],
    )


class HeroBlock(BaseContentBlock):
    style_key = "hero"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock()
    intro = blocks.TextBlock(label=_("Supporting text"), required=False, max_length=300)
    buttons = button_list()
    image = ImageBlock(
        label=_("Image"),
        required=False,
        help_text=_("Shown behind the text. Use a wide photo."),
    )

    def get_preview_value(self):
        return with_sample_images(super().get_preview_value(), image="landscape-1.webp")

    class Meta:
        icon = "image"
        label = _("Hero")
        description = _(
            "The large opening section of a page, with a title, a short text, buttons "
            "and an optional image."
        )
        template = "orion/blocks/hero.html"
        preview_value = {
            "title": "<p>Everything you need, <b>close to you</b></p>",
            "intro": "A short text that explains what the page is about.",
            "buttons": [{"label": "Contact us", "url": "https://example.com/"}],
        }


class TextContentBlock(BaseContentBlock):
    style_key = "text"

    body = RichTextBodyBlock()

    class Meta:
        icon = "pilcrow"
        label = _("Text")
        description = _("Paragraphs with bold, italics, links, lists and subtitles.")
        template = "orion/blocks/text.html"
        preview_value = {
            "body": "<h2>A subtitle</h2><p>Write here as in any word processor, with "
            "<b>bold</b>, <i>italics</i> and lists.</p><ul><li>First item</li>"
            "<li>Second item</li></ul>",
        }


class ImageContentBlock(BaseContentBlock):
    style_key = "image"

    image = ImageBlock(label=_("Image"))
    caption = blocks.CharBlock(label=_("Caption"), required=False, max_length=200)

    def get_preview_value(self):
        return with_sample_images(super().get_preview_value(), image="landscape-2.webp")

    class Meta:
        icon = "image"
        label = _("Image")
        description = _("A photo with an optional caption.")
        template = "orion/blocks/image.html"
        preview_value = {"caption": "A photo with its caption."}


class GalleryImageBlock(blocks.StructBlock):
    image = ImageBlock(label=_("Image"))
    caption = blocks.CharBlock(label=_("Caption"), required=False, max_length=200)

    class Meta:
        icon = "image"
        label = _("Image")


class GalleryBlock(BaseContentBlock):
    style_key = "gallery"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    images = blocks.ListBlock(
        GalleryImageBlock(), label=_("Images"), min_num=2, max_num=24
    )

    def get_preview_value(self):
        return with_sample_images(
            super().get_preview_value(),
            images=["landscape-1.webp", "landscape-2.webp", "landscape-3.webp"],
        )

    class Meta:
        icon = "image"
        label = _("Gallery")
        description = _("A grid of photos with optional captions.")
        template = "orion/blocks/gallery.html"
        preview_value = {
            "images": [{"caption": "First photo"}, {}, {"caption": "Third photo"}]
        }


class ImageTextBlock(BaseContentBlock):
    style_key = "image_text"

    image = ImageBlock(label=_("Image"))
    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock()
    body = RichTextBodyBlock(required=False)
    buttons = button_list()
    image_position = blocks.ChoiceBlock(
        label=_("Image position"),
        choices=[("left", _("Left")), ("right", _("Right"))],
        default="left",
    )

    def get_preview_value(self):
        return with_sample_images(super().get_preview_value(), image="landscape-3.webp")

    class Meta:
        icon = "image"
        label = _("Image and text")
        description = _("A photo next to a title, a text and buttons.")
        template = "orion/blocks/image_text.html"
        preview_value = {
            "title": "<p>A photo next to <b>a text</b></p>",
            "body": "<p>A short text that goes with the photo.</p>",
            "buttons": [{"label": "Learn more", "url": "https://example.com/"}],
        }


class CardBlock(blocks.StructBlock):
    image = ImageBlock(label=_("Image"), required=False)
    title = blocks.CharBlock(label=_("Title"), max_length=100)
    text = blocks.TextBlock(label=_("Text"), required=False, max_length=400)
    link = LinkBlock(
        label=_("Link"),
        require_destination=False,
        help_text=_("Optional. The text defaults to the page title."),
    )
    tag = blocks.CharBlock(
        label=_("Tag"),
        required=False,
        max_length=40,
        help_text=_("Optional. A short label shown above the title."),
    )

    class Meta:
        icon = "doc-full"
        label = _("Card")


class CardsBlock(BaseContentBlock):
    style_key = "cards"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    columns = blocks.ChoiceBlock(
        label=_("Columns"),
        choices=[("2", "2"), ("3", "3"), ("4", "4")],
        default="3",
    )
    cards = blocks.ListBlock(CardBlock(), label=_("Cards"), min_num=1)
    image_fit = blocks.ChoiceBlock(
        label=_("Images"),
        choices=[
            ("cover", _("Cropped to fill the space")),
            ("contain", _("Whole image, uncropped")),
        ],
        default="cover",
        help_text=_("Use the whole image for illustrations and logos."),
    )

    def get_preview_value(self):
        return with_sample_images(
            super().get_preview_value(),
            cards=["landscape-1.webp", "landscape-2.webp", "landscape-3.webp"],
        )

    class Meta:
        icon = "table"
        label = _("Cards")
        description = _(
            "A grid of cards, each with an optional image, a text and a link."
        )
        template = "orion/blocks/cards.html"
        preview_value = {
            "title": "<p>Our <b>services</b></p>",
            "columns": "3",
            "cards": [
                {"title": "First service", "text": "A short description."},
                {"title": "Second service", "text": "A short description."},
                {"title": "Third service", "text": "A short description."},
            ],
        }


class StatBlock(blocks.StructBlock):
    number = blocks.IntegerBlock(label=_("Number"), min_value=0)
    prefix = blocks.CharBlock(
        label=_("Before the number"), required=False, max_length=5, help_text="+"
    )
    suffix = blocks.CharBlock(
        label=_("After the number"), required=False, max_length=5, help_text="%"
    )
    label = blocks.CharBlock(label=_("Text"), max_length=80)

    class Meta:
        icon = "order"
        label = _("Figure")


class StatsBlock(BaseContentBlock):
    style_key = "stats"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    stats = blocks.ListBlock(StatBlock(), label=_("Figures"), min_num=1, max_num=4)

    class Meta:
        icon = "order"
        label = _("Figures")
        description = _("Large numbers that count up when they appear on screen.")
        template = "orion/blocks/stats.html"
        preview_value = {
            "title": "<p><b>30 years</b> of experience</p>",
            "stats": [
                {"number": 40, "prefix": "+", "label": "specialties"},
                {"number": 180, "prefix": "+", "label": "professionals"},
                {"number": 98, "suffix": "%", "label": "satisfied patients"},
            ],
        }


class PanelBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"), max_length=120)
    body = RichTextBodyBlock()


class TabPanelBlock(PanelBlock):
    class Meta:
        icon = "doc-full"
        label = _("Tab")


class AccordionItemBlock(PanelBlock):
    title = blocks.CharBlock(label=_("Question"), max_length=200)
    body = RichTextBodyBlock(label=_("Answer"))

    class Meta:
        icon = "help"
        label = _("Question")


def _with_block_id(context, parent_context):
    # The page body passes the StreamField id; a block rendered alone (such as in the
    # editor preview) gets a random one.
    context["block_id"] = (parent_context or {}).get("block_id") or uuid.uuid4().hex
    return context


class TabsBlock(BaseContentBlock):
    style_key = "tabs"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    tabs = blocks.ListBlock(TabPanelBlock(), label=_("Tabs"), min_num=2, max_num=6)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)
        return _with_block_id(context, parent_context)

    class Meta:
        icon = "folder-open-inverse"
        label = _("Tabs")
        description = _("Content split into tabs; only one tab is shown at a time.")
        template = "orion/blocks/tabs.html"
        preview_value = {
            "tabs": [
                {"title": "First tab", "body": "<p>Content of the first tab.</p>"},
                {"title": "Second tab", "body": "<p>Content of the second tab.</p>"},
            ],
        }


class AccordionBlock(BaseContentBlock):
    style_key = "accordion"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    items = blocks.ListBlock(AccordionItemBlock(), label=_("Questions"), min_num=1)

    class Meta:
        icon = "help"
        label = _("Accordion")
        description = _("Questions that open to show their answer, such as an FAQ.")
        template = "orion/blocks/accordion.html"
        preview_value = {
            "title": "<p>Frequently asked <b>questions</b></p>",
            "items": [
                {"title": "How do I book?", "body": "<p>Call us or write to us.</p>"},
                {"title": "Where are you?", "body": "<p>See our contact page.</p>"},
            ],
        }


class CallToActionBlock(BaseContentBlock):
    style_key = "call_to_action"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock()
    text = blocks.TextBlock(label=_("Text"), required=False, max_length=300)
    buttons = button_list(min_num=1)

    class Meta:
        icon = "pick"
        label = _("Call to action")
        description = _(
            "A highlighted box that invites visitors to take the next step."
        )
        template = "orion/blocks/call_to_action.html"
        preview_value = {
            "title": "<p>Ready to <b>get started</b>?</p>",
            "text": "A short text that invites the next step.",
            "buttons": [{"label": "Contact us", "url": "https://example.com/"}],
        }


class LogoBlock(blocks.StructBlock):
    image = ImageChooserBlock(label=_("Logo"))
    name = blocks.CharBlock(
        label=_("Name"),
        max_length=100,
        help_text=_("Read by screen readers and shown if the image fails to load."),
    )
    url = blocks.URLBlock(label=_("Website"), required=False)

    class Meta:
        icon = "image"
        label = _("Logo")


class LogosBlock(BaseContentBlock):
    style_key = "logos"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    logos = blocks.ListBlock(LogoBlock(), label=_("Logos"), min_num=1)

    def get_preview_value(self):
        return with_sample_images(
            super().get_preview_value(),
            logos=["logo-1.svg", "logo-2.svg", "logo-3.svg", "logo-4.svg"],
        )

    class Meta:
        icon = "site"
        label = _("Logos")
        description = _(
            "A row of logos, such as partners or clients, with optional links."
        )
        template = "orion/blocks/logos.html"
        preview_value = {
            "title": "<p>Our <b>partners</b></p>",
            "logos": [
                {"name": "Partner 1"},
                {"name": "Partner 2"},
                {"name": "Partner 3"},
                {"name": "Partner 4"},
            ],
        }


class ContactItemBlock(blocks.StructBlock):
    label = blocks.CharBlock(
        label=_("Label"), max_length=60, help_text=_("Opening hours")
    )
    text = blocks.TextBlock(label=_("Text"), max_length=300)

    class Meta:
        icon = "info-circle"
        label = _("Extra item")


class ContactBlock(BaseContentBlock):
    style_key = "contact"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    show_phone = blocks.BooleanBlock(label=_("Phone"), default=True, required=False)
    show_whatsapp = blocks.BooleanBlock(
        label=_("WhatsApp"), default=True, required=False
    )
    show_email = blocks.BooleanBlock(label=_("Email"), default=True, required=False)
    show_address = blocks.BooleanBlock(label=_("Address"), default=True, required=False)
    extra_items = blocks.ListBlock(
        ContactItemBlock(), label=_("Extra items"), default=[], min_num=0
    )

    def get_context(self, value, parent_context=None):
        # Imported here: the settings model's app may load after the blocks module.
        from orion.site_data.models import CONTACT_FIELDS, SiteSettings

        context = super().get_context(value, parent_context)
        context["site_items"] = SiteSettings.load().contact_items(
            [name for name in CONTACT_FIELDS if value.get(f"show_{name}", True)]
        )
        return context

    class Meta:
        icon = "mail"
        label = _("Contact details")
        description = _(
            "The site's phone, WhatsApp, email and address from Site data, plus extra "
            "items such as opening hours."
        )
        template = "orion/blocks/contact.html"
        preview_value = {
            "title": "<p>Get in <b>touch</b></p>",
            "extra_items": [
                {"label": "Opening hours", "text": "Monday to Friday, 8 to 18"}
            ],
        }


class ButtonsBlock(BaseContentBlock):
    style_key = "buttons"

    buttons = button_list(min_num=1, max_num=3)
    alignment = blocks.ChoiceBlock(
        label=_("Alignment"),
        choices=[("left", _("Left")), ("center", _("Center")), ("right", _("Right"))],
        default="left",
    )

    class Meta:
        icon = "link"
        label = _("Buttons")
        description = _("One to three buttons in a row.")
        template = "orion/blocks/buttons.html"
        preview_value = {
            "buttons": [
                {"label": "Primary", "url": "https://example.com/"},
                {
                    "label": "Secondary",
                    "url": "https://example.com/",
                    "variant": "secondary",
                },
            ],
        }


def sample_articles(count):
    """Articles for the latest articles preview, which must not touch the database."""
    images = ["landscape-1.webp", "landscape-2.webp", "landscape-3.webp"]
    today = timezone.localdate()
    return [
        SimpleNamespace(
            title=f"Sample article {number}",
            date=today - datetime.timedelta(days=number * 7),
            summary="A short summary that invites people to read the article.",
            image=SampleImage(images[(number - 1) % len(images)]),
            image_alt_text="",
            url="#",
        )
        for number in range(1, count + 1)
    ]


class LatestArticlesBlock(BaseContentBlock):
    style_key = "latest_articles"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    count = blocks.IntegerBlock(
        label=_("How many"), default=3, min_value=1, max_value=12
    )
    index = blocks.PageChooserBlock(
        page_type="orion_pages.ArticleIndexPage",
        label=_("Listing"),
        required=False,
        help_text=_("Optional. Without a listing, shows articles from all of them."),
    )

    def get_preview_context(self, value, parent_context=None):
        context = super().get_preview_context(value, parent_context)
        context["is_block_preview"] = True
        return context

    def get_context(self, value, parent_context=None):
        # Imported here: the pages app imports these blocks for its models.
        from orion.pages.models import ArticlePage

        context = super().get_context(value, parent_context)
        if (parent_context or {}).get("is_block_preview"):
            # Previews show sample articles: a new site has none.
            context["articles"] = sample_articles(value.get("count") or 3)
            return context
        index = value.get("index")
        if index is not None:
            # The listing chosen in the original, in the visitor's language.
            index = index.localized
            context["index"] = index if index.live else None
        context["articles"] = ArticlePage.objects.latest(
            index=index, limit=value.get("count") or 3
        )
        return context

    class Meta:
        icon = "doc-full-inverse"
        label = _("Latest articles")
        description = _("The most recent articles, from every listing or from one.")
        template = "orion/blocks/latest_articles.html"


class FormBlock(BaseContentBlock):
    style_key = "form"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    form_page = blocks.PageChooserBlock(
        page_type="orion_forms.FormPage",
        label=_("Form"),
        help_text=_("Submissions arrive at the form's page, as if sent from there."),
    )

    def get_preview_context(self, value, parent_context=None):
        context = super().get_preview_context(value, parent_context)
        context["is_block_preview"] = True
        return context

    def get_context(self, value, parent_context=None):
        # Imported here: the forms app imports these blocks through the page models.
        from orion.forms.models import sample_form

        context = super().get_context(value, parent_context)
        parent_context = parent_context or {}
        if parent_context.get("is_block_preview"):
            context["form"], context["action"] = sample_form(), "#"
            return context
        form_page = value.get("form_page")
        form_page = form_page.localized.specific if form_page is not None else None
        if form_page is None or not form_page.live:
            return context
        request = parent_context.get("request")
        context["form"] = form_page.get_form(
            page=form_page, user=getattr(request, "user", None)
        )
        context["action"] = form_page.url
        return context

    class Meta:
        icon = "form"
        label = _("Form")
        description = _("A form created in Pages, to fill in from this page.")
        template = "orion/blocks/form.html"


class LocationBlock(blocks.FieldBlock):
    """A point on the map, as ``{"lat": float, "lng": float}``."""

    def __init__(self, required=True, help_text=None, **kwargs):
        self.field = LocationField(required=required, help_text=help_text)
        super().__init__(**kwargs)

    # The widget's hidden input holds the location as JSON text: the form posts that
    # text, and the stored value is the decoded object.
    def value_for_form(self, value):
        return value if isinstance(value, str) else self.field.prepare_value(value)

    def value_from_form(self, value):
        if not isinstance(value, str):
            return value
        try:
            return json.loads(value) if value else None
        except ValueError:
            # Left as text, so that validation reports it.
            return value

    class Meta:
        icon = "site"


class MapPointBlock(blocks.StructBlock):
    location = LocationBlock(label=_("Location"))
    name = blocks.CharBlock(label=_("Name"), max_length=100)
    description = blocks.TextBlock(
        label=_("Description"),
        required=False,
        max_length=300,
        help_text=_("For example, the address or the opening hours."),
    )

    class Meta:
        icon = "site"
        label = _("Point")


class MapBlock(BaseContentBlock):
    style_key = "map"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    include_site_location = blocks.BooleanBlock(
        label=_("Include the site location"),
        default=True,
        required=False,
        help_text=_("The location set in Site data."),
    )
    points = blocks.ListBlock(MapPointBlock(), label=_("Points"), default=[], min_num=0)
    zoom = blocks.IntegerBlock(
        label=_("Zoom"),
        default=16,
        min_value=1,
        max_value=19,
        help_text=_("Used with a single point; several points are all shown."),
    )

    def get_context(self, value, parent_context=None):
        # Imported here: the settings model's app may load after the blocks module.
        from wagtail.models import Site

        from orion.site_data.models import SiteSettings

        context = super().get_context(value, parent_context)
        points = []
        if value.get("include_site_location", True):
            request = (parent_context or {}).get("request")
            site = Site.find_for_request(request) if request else None
            site_point = SiteSettings.load().map_point(
                name=site.site_name if site else ""
            )
            if site_point:
                points.append(site_point)
        points += [
            {
                **point["location"],
                "name": point["name"],
                "description": point.get("description") or "",
            }
            for point in value.get("points") or []
            if point.get("location")
        ]
        context["points"] = points
        context["zoom"] = value.get("zoom") or 16
        return context

    class Meta:
        icon = "site"
        label = _("Map")
        description = _(
            "A map with the site location and other points, loaded when the visitor "
            "asks for it."
        )
        template = "orion/blocks/map.html"
        preview_value = {
            "include_site_location": False,
            "points": [
                {
                    "location": {"lat": -25.2637, "lng": -57.5759},
                    "name": "Example point",
                    "description": "An address or the opening hours.",
                }
            ],
        }


class VideoChooserBlock(DocumentChooserBlock):
    """A document of the library that must be a video."""

    def clean(self, value):
        value = super().clean(value)
        if value and value.file_extension.lower() not in VIDEO_EXTENSIONS:
            raise ValidationError(_("Choose an MP4 or WebM video."))
        return value


class VideoBlock(BaseContentBlock):
    style_key = "video"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    video = VideoChooserBlock(
        label=_("Video"),
        help_text=_(
            "An MP4 or WebM from the document library, in a public collection."
        ),
    )
    cover = ImageBlock(
        label=_("Cover image"),
        help_text=_("Shown until the video plays."),
    )
    mode = blocks.ChoiceBlock(
        label=_("Playback"),
        choices=[
            ("controls", _("With controls: the visitor starts it, with sound")),
            ("ambient", _("Ambient: muted and looping while on screen")),
        ],
        default="controls",
    )
    orientation = blocks.ChoiceBlock(
        label=_("Format"),
        choices=[
            ("landscape", _("Landscape (16:9)")),
            ("portrait", _("Vertical (9:16)")),
        ],
        default="landscape",
    )
    caption = blocks.CharBlock(label=_("Caption"), required=False, max_length=200)

    def get_preview_value(self):
        return with_sample_images(super().get_preview_value(), cover="landscape-1.webp")

    class Meta:
        icon = "media"
        label = _("Video")
        description = _("A video from the library, with a cover image.")
        template = "orion/blocks/video.html"
        preview_value = {"caption": "A video with its caption."}


class CarouselSlideBlock(blocks.StructBlock):
    image = ImageBlock(label=_("Image"))
    video = VideoChooserBlock(
        label=_("Video"),
        required=False,
        help_text=_("Optional. Plays muted and looping; the image is its cover."),
    )
    title = blocks.CharBlock(label=_("Title"), required=False, max_length=120)
    text = blocks.TextBlock(label=_("Text"), required=False, max_length=300)
    link = LinkBlock(
        label=_("Link"),
        require_destination=False,
        help_text=_("Optional. The text defaults to the page title."),
    )

    class Meta:
        icon = "image"
        label = _("Slide")


class CarouselBlock(BaseContentBlock):
    style_key = "carousel"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    layout = blocks.ChoiceBlock(
        label=_("Arrangement"),
        choices=[
            ("full", _("One slide across the full width")),
            ("cards", _("Several cards at a time")),
        ],
        default="full",
    )
    slides = blocks.ListBlock(
        CarouselSlideBlock(), label=_("Slides"), min_num=2, max_num=12
    )

    def get_preview_value(self):
        return with_sample_images(
            super().get_preview_value(),
            slides=["landscape-1.webp", "landscape-2.webp", "landscape-3.webp"],
        )

    class Meta:
        icon = "image"
        label = _("Carousel")
        description = _(
            "Slides that the visitor moves through, one or several at a time."
        )
        template = "orion/blocks/carousel.html"
        preview_value = {
            "layout": "full",
            "slides": [
                {"title": "First slide", "text": "A short message."},
                {"title": "Second slide", "text": "A short message."},
                {"title": "Third slide", "text": "A short message."},
            ],
        }


class StepBlock(blocks.StructBlock):
    title = blocks.CharBlock(label=_("Title"), max_length=80)
    text = blocks.TextBlock(label=_("Text"), required=False, max_length=300)
    image = ImageBlock(label=_("Image"), required=False)

    class Meta:
        icon = "list-ol"
        label = _("Step")


class StepsBlock(BaseContentBlock):
    style_key = "steps"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    steps = blocks.ListBlock(
        StepBlock(),
        label=_("Steps"),
        min_num=2,
        max_num=12,
        help_text=_("They are numbered automatically, in this order."),
    )

    class Meta:
        icon = "list-ol"
        label = _("Steps")
        description = _("Numbered steps, one after the other, such as a process.")
        template = "orion/blocks/steps.html"
        preview_value = {
            "title": "<p>How it <b>works</b></p>",
            "steps": [
                {"title": "First step", "text": "A short description."},
                {"title": "Second step", "text": "A short description."},
                {"title": "Third step", "text": "A short description."},
            ],
        }


class CountdownBlock(BaseContentBlock):
    style_key = "countdown"

    eyebrow = EyebrowBlock()
    title = HighlightedTitleBlock(required=False)
    deadline = blocks.DateTimeBlock(
        label=_("Deadline"),
        help_text=_("The countdown ends at this date and time."),
    )
    closed_message = blocks.CharBlock(
        label=_("Message when it ends"),
        required=False,
        max_length=200,
        help_text=_("Optional. Replaces the countdown once the deadline has passed."),
    )
    buttons = button_list(max_num=1)

    class Meta:
        icon = "time"
        label = _("Countdown")
        description = _("The time left until a deadline, with an optional button.")
        template = "orion/blocks/countdown.html"
        preview_value = {
            "title": "<p>Applications <b>close soon</b></p>",
            "deadline": "2099-12-31T23:59:00+00:00",
        }


class MarqueeLogoBlock(blocks.StructBlock):
    image = ImageChooserBlock(label=_("Logo"))
    name = blocks.CharBlock(
        label=_("Name"),
        max_length=100,
        help_text=_("Read by screen readers and shown if the image fails to load."),
    )

    class Meta:
        icon = "image"
        label = _("Logo")


class MarqueeBlock(BaseContentBlock):
    style_key = "marquee"

    phrases = blocks.ListBlock(
        blocks.CharBlock(max_length=40),
        label=_("Phrases"),
        required=False,
        default=[],
        max_num=12,
    )
    logos = blocks.ListBlock(
        MarqueeLogoBlock(),
        label=_("Logos"),
        required=False,
        default=[],
        max_num=12,
    )
    speed = blocks.ChoiceBlock(
        label=_("Speed"),
        choices=[
            ("slow", _("Slow")),
            ("normal", _("Normal")),
            ("fast", _("Fast")),
        ],
        default="normal",
    )

    def clean(self, value):
        value = super().clean(value)
        if not value["phrases"] and not value["logos"]:
            raise blocks.StructBlockValidationError(
                non_block_errors=[
                    ValidationError(_("Add at least one phrase or one logo."))
                ]
            )
        return value

    def get_preview_value(self):
        return with_sample_images(
            super().get_preview_value(),
            logos=["logo-1.svg", "logo-2.svg", "logo-3.svg"],
        )

    class Meta:
        icon = "repeat"
        label = _("Marquee")
        description = _(
            "Short phrases and logos that slide in a loop, with a pause button."
        )
        template = "orion/blocks/marquee.html"
        preview_value = {
            "phrases": ["A short phrase", "Another phrase"],
            "logos": [{"name": "Logo 1"}, {"name": "Logo 2"}, {"name": "Logo 3"}],
        }


class ContentStreamBlock(blocks.StreamBlock):
    """Every Orion content block, ready to use as a page body.

    Render it with ``{% include_block page.body %}``: that skips hidden blocks. A
    template that loops over the body itself must skip blocks whose ``is_visible`` is
    off.
    """

    hero = HeroBlock()
    text = TextContentBlock()
    image = ImageContentBlock()
    gallery = GalleryBlock()
    image_text = ImageTextBlock()
    cards = CardsBlock()
    stats = StatsBlock()
    tabs = TabsBlock()
    accordion = AccordionBlock()
    call_to_action = CallToActionBlock()
    logos = LogosBlock()
    contact = ContactBlock()
    buttons = ButtonsBlock()
    latest_articles = LatestArticlesBlock()
    map = MapBlock()
    form = FormBlock()
    video = VideoBlock()
    carousel = CarouselBlock()
    steps = StepsBlock()
    countdown = CountdownBlock()
    marquee = MarqueeBlock()

    def clean(self, value):
        # The hero holds the page's h1, so it can only open the body.
        value = super().clean(value)
        block_errors = {
            index: ValidationError(_("The hero must be the first block."))
            for index, child in enumerate(value)
            if child.block_type == "hero" and index > 0
        }
        # Hidden blocks count too: they can be shown again.
        seen_anchors = set()
        for index, child in enumerate(value):
            anchor = get_anchor(child.value)
            if not anchor:
                continue
            if anchor in RESERVED_ANCHORS:
                block_errors[index] = ValidationError(
                    _("This anchor is reserved by the site. Choose another one.")
                )
            elif anchor in seen_anchors:
                block_errors[index] = ValidationError(
                    _("Another block of this page already uses this anchor.")
                )
            seen_anchors.add(anchor)
        if block_errors:
            raise blocks.StreamBlockValidationError(block_errors=block_errors)
        return value

    def render_basic(self, value, context=None):
        parent_context = dict(context or {})
        rendered_children = [
            (
                child.block_type,
                get_anchor(child.value),
                get_style(child.value),
                child.block.render(
                    child.value,
                    context={
                        **parent_context,
                        "block_id": child.id,
                        "is_leading_block": position == 0,
                    },
                ),
            )
            for position, child in enumerate(
                child for child in value if is_visible(child.value)
            )
        ]
        # A block may render nothing, such as latest articles without articles.
        rendered_children = [child for child in rendered_children if child[3].strip()]
        # The editor's preview shows every block, so nothing waits to be revealed.
        request = parent_context.get("request")
        reveals = settings.ORION_BLOCK_REVEAL and not getattr(
            request, "is_preview", False
        )
        # The style goes on the wrapper too, so a project can paint the block's band
        # edge to edge. An attribute, not a class: projects already style the class.
        # The first block is never revealed: it is what the visitor sees first.
        return format_html_join(
            "\n",
            '<div class="block-{}"{}{}{}>{}</div>',
            [
                (
                    name,
                    format_html(' id="{}"', anchor) if anchor else "",
                    format_html(' data-block-style="{}"', style) if style else "",
                    mark_safe(" data-reveal") if reveals and position > 0 else "",
                    html,
                )
                for position, (name, anchor, style, html) in enumerate(
                    rendered_children
                )
            ],
        )


class SiteStreamBlock(ContentStreamBlock):
    """Orion's blocks plus the project's (ORION_PROJECT_BLOCKS), for page bodies."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, path in settings.ORION_PROJECT_BLOCKS.items():
            block = import_string(path)()
            block.set_name(name)
            self.child_blocks[name] = block


class BodyStreamField(StreamField):
    """A StreamField whose migrations ignore the project's blocks.

    It describes itself with Orion's blocks only, so that declaring blocks in a project
    does not make ``makemigrations`` write inside the installed package.
    """

    def deconstruct(self):
        name, _path, _args, kwargs = super().deconstruct()
        _name, path, args, plain_kwargs = StreamField(
            ContentStreamBlock()
        ).deconstruct()
        return name, path, args, {**kwargs, **plain_kwargs}


def get_anchor(value):
    """A block value's anchor; blocks without the field have none."""
    return getattr(value, "get", lambda *_args: None)("anchor")


def get_style(value):
    """The style a block value uses, unless it is the default one."""
    style = getattr(value, "get", lambda *_args: None)("style")
    return None if style in (None, DEFAULT_STYLE) else style


def is_visible(value):
    """Whether a block value should be shown; blocks without the field always are."""
    return getattr(value, "get", lambda *_args: True)("is_visible", True) is not False
