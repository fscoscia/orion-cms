"""StreamField blocks shared by Orion's apps."""

import re
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.blocks import StructBlockValidationError
from wagtail.models import Site

DESTINATION_FIELDS = ("page", "url", "email", "phone")
PHONE_PATTERN = re.compile(r"^\+?[\d\s().-]{6,30}$")


def normalize_phone(phone: str) -> str:
    """Return the phone as digits, keeping a leading plus sign for ``tel:`` links."""
    digits = re.sub(r"\D", "", phone)
    return f"+{digits}" if phone.strip().startswith("+") else digits


def get_site_hostnames() -> set[str]:
    return {
        hostname.lower() for hostname in Site.objects.values_list("hostname", flat=True)
    }


class LinkValue(blocks.StructValue):
    """A link with exactly one destination, resolved for the current visitor.

    The resolved values are named ``href`` and ``linked_page`` because templates look
    up dictionary keys first, so ``link.url`` or ``link.page`` would return the raw
    fields instead.
    """

    @cached_property
    def linked_page(self):
        """The published version of the chosen page in the active language, if any."""
        chosen_page = self.get("page")
        if chosen_page is None:
            return None
        translated_page = chosen_page.localized
        if translated_page.live:
            return translated_page.specific
        return chosen_page.specific if chosen_page.live else None

    @cached_property
    def href(self) -> str | None:
        if self.get("page") is not None:
            return self.linked_page.url if self.linked_page is not None else None
        if self.get("url"):
            return self["url"]
        if self.get("email"):
            return f"mailto:{self['email']}"
        if self.get("phone"):
            return f"tel:{normalize_phone(self['phone'])}"
        return None

    @property
    def text(self) -> str:
        """The visible text: the label, or the page title, email or phone."""
        if self.get("label"):
            return self["label"]
        if self.linked_page is not None:
            return self.linked_page.title
        return self.get("email") or self.get("phone") or self.get("url") or ""

    @property
    def is_visible(self) -> bool:
        return self.href is not None

    @property
    def is_external(self) -> bool:
        return bool(self.get("url")) and self.get("page") is None

    @property
    def opens_in_new_tab(self) -> bool:
        return self.is_external and bool(self.get("open_in_new_tab"))

    def has_page(self, page) -> bool:
        """Whether this link points to ``page`` or one of its ancestors."""
        linked_page = self.linked_page
        if linked_page is None or page is None:
            return False
        return page.pk == linked_page.pk or page.is_descendant_of(linked_page)


class LinkBlock(blocks.StructBlock):
    """A link to a page, an external URL, an email address or a phone number.

    Pass ``require_destination=False`` for links that may act as a plain label, such
    as a menu item that only groups its subitems.
    """

    label = blocks.CharBlock(
        label=_("Text"),
        required=False,
        max_length=80,
        help_text=_("Leave empty to use the page title, email or phone."),
    )
    page = blocks.PageChooserBlock(label=_("Page"), required=False)
    url = blocks.URLBlock(label=_("External URL"), required=False)
    email = blocks.EmailBlock(label=_("Email"), required=False)
    phone = blocks.CharBlock(label=_("Phone"), required=False, max_length=30)
    open_in_new_tab = blocks.BooleanBlock(
        label=_("Open in a new tab"),
        required=False,
        help_text=_("Only applies to external URLs."),
    )

    def __init__(self, *args, require_destination=True, **kwargs):
        self.require_destination = require_destination
        super().__init__(*args, **kwargs)

    def clean(self, value):
        value = super().clean(value)
        destinations = [name for name in DESTINATION_FIELDS if value.get(name)]
        block_errors = {}

        if len(destinations) > 1:
            raise StructBlockValidationError(
                non_block_errors=[
                    ValidationError(
                        _(
                            "Choose only one destination: a page, a URL, an email "
                            "or a phone."
                        )
                    )
                ]
            )
        if not destinations and self.require_destination:
            raise StructBlockValidationError(
                non_block_errors=[
                    ValidationError(
                        _("Choose a destination: a page, a URL, an email or a phone.")
                    )
                ]
            )

        if value.get("url"):
            hostname = (urlsplit(value["url"]).hostname or "").lower()
            if hostname in get_site_hostnames():
                block_errors["url"] = ValidationError(
                    _("This address belongs to this site. Choose the page instead.")
                )
        if value.get("phone") and not PHONE_PATTERN.match(value["phone"]):
            block_errors["phone"] = ValidationError(
                _("Enter a phone number using digits, spaces, '+', '-' or parentheses.")
            )
        if block_errors:
            raise StructBlockValidationError(block_errors=block_errors)
        return value

    class Meta:
        icon = "link"
        label = _("Link")
        value_class = LinkValue
        form_classname = "orion-link-block"
