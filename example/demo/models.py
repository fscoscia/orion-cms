"""A page to develop and test Orion's content blocks; it never ships with Orion."""

from wagtail.admin.panels import FieldPanel
from wagtail.fields import StreamField
from wagtail.models import Page

from orion.core.blocks import ContentStreamBlock


class DemoPage(Page):
    body = StreamField(ContentStreamBlock(), blank=True, verbose_name="body")

    content_panels = [*Page.content_panels, FieldPanel("body")]
