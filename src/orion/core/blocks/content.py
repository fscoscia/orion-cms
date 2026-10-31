"""Content blocks that editors use to build pages.

Block keys and field names are a StreamField contract: renaming or removing one once
there is content requires a data migration.
"""

import functools
import re
import uuid

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.admin.telepath import register
from wagtail.admin.telepath.widgets import WidgetAdapter
from wagtail.blocks.struct_block import BlockGroup
from wagtail.images.blocks import ImageBlock, ImageChooserBlock

from orion.core.blocks.links import LinkBlock

DEFAULT_STYLE = "default"
RICH_TEXT_FEATURES = ["h2", "h3", "bold", "italic", "link", "ol", "ul"]
PARAGRAPH_PATTERN = re.compile(r"<p[\s>]")


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
    """Base of Orion's content blocks: adds the "Style" and "Visible" fields.

    Both go last and, in the editor, in the block's collapsible settings area.
    Subclasses set ``style_key``, the key projects use in ORION_BLOCK_STYLES.
    """

    style_key = None
    settings_block_names = ("style", "is_visible")

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
        # Passed to the constructor, which builds the editor's form layout.
        super().__init__(
            [
                *(local_blocks or []),
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

    title = HighlightedTitleBlock()
    intro = blocks.TextBlock(label=_("Supporting text"), required=False, max_length=300)
    buttons = button_list()
    image = ImageBlock(
        label=_("Image"),
        required=False,
        help_text=_("Shown behind the text. Use a wide photo."),
    )

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

    class Meta:
        icon = "image"
        label = _("Image")
        description = _("A photo with an optional caption.")
        template = "orion/blocks/image.html"


class GalleryImageBlock(blocks.StructBlock):
    image = ImageBlock(label=_("Image"))
    caption = blocks.CharBlock(label=_("Caption"), required=False, max_length=200)

    class Meta:
        icon = "image"
        label = _("Image")


class GalleryBlock(BaseContentBlock):
    style_key = "gallery"

    title = HighlightedTitleBlock(required=False)
    images = blocks.ListBlock(
        GalleryImageBlock(), label=_("Images"), min_num=2, max_num=24
    )

    class Meta:
        icon = "image"
        label = _("Gallery")
        description = _("A grid of photos with optional captions.")
        template = "orion/blocks/gallery.html"


class ImageTextBlock(BaseContentBlock):
    style_key = "image_text"

    image = ImageBlock(label=_("Image"))
    title = HighlightedTitleBlock()
    body = RichTextBodyBlock(required=False)
    buttons = button_list()
    image_position = blocks.ChoiceBlock(
        label=_("Image position"),
        choices=[("left", _("Left")), ("right", _("Right"))],
        default="left",
    )

    class Meta:
        icon = "image"
        label = _("Image and text")
        description = _("A photo next to a title, a text and buttons.")
        template = "orion/blocks/image_text.html"


class CardBlock(blocks.StructBlock):
    image = ImageBlock(label=_("Image"), required=False)
    title = blocks.CharBlock(label=_("Title"), max_length=100)
    text = blocks.TextBlock(label=_("Text"), required=False, max_length=400)
    link = LinkBlock(
        label=_("Link"),
        require_destination=False,
        help_text=_("Optional. The text defaults to the page title."),
    )

    class Meta:
        icon = "doc-full"
        label = _("Card")


class CardsBlock(BaseContentBlock):
    style_key = "cards"

    title = HighlightedTitleBlock(required=False)
    columns = blocks.ChoiceBlock(
        label=_("Columns"),
        choices=[("2", "2"), ("3", "3"), ("4", "4")],
        default="3",
    )
    cards = blocks.ListBlock(CardBlock(), label=_("Cards"), min_num=1)

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

    title = HighlightedTitleBlock(required=False)
    logos = blocks.ListBlock(LogoBlock(), label=_("Logos"), min_num=1)

    class Meta:
        icon = "site"
        label = _("Logos")
        description = _(
            "A row of logos, such as partners or clients, with optional links."
        )
        template = "orion/blocks/logos.html"


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


class LatestArticlesBlock(BaseContentBlock):
    style_key = "latest_articles"

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

    def get_context(self, value, parent_context=None):
        # Imported here: the pages app imports these blocks for its models.
        from orion.pages.models import ArticlePage

        context = super().get_context(value, parent_context)
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

    def clean(self, value):
        # The hero holds the page's h1, so it can only open the body.
        value = super().clean(value)
        misplaced_heroes = {
            index: ValidationError(_("The hero must be the first block."))
            for index, child in enumerate(value)
            if child.block_type == "hero" and index > 0
        }
        if misplaced_heroes:
            raise blocks.StreamBlockValidationError(block_errors=misplaced_heroes)
        return value

    def render_basic(self, value, context=None):
        parent_context = dict(context or {})
        rendered_children = [
            (
                child.block_type,
                child.block.render(
                    child.value, context={**parent_context, "block_id": child.id}
                ),
            )
            for child in value
            if is_visible(child.value)
        ]
        # A block may render nothing, such as latest articles without articles.
        return format_html_join(
            "\n",
            '<div class="block-{}">{}</div>',
            [(name, html) for name, html in rendered_children if html.strip()],
        )


def is_visible(value):
    """Whether a block value should be shown; blocks without the field always are."""
    return getattr(value, "get", lambda *_args: True)("is_visible", True) is not False
