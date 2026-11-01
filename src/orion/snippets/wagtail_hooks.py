from django import forms
from django.conf import settings
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel, MultipleChooserPanel
from wagtail.admin.ui.tables import BooleanColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import IndexView, SnippetViewSet

from orion.snippets.models import CodeSnippet

DISABLED_MESSAGE = _(
    "ORION_SCRIPTS_DISABLED is on: no code snippet is loaded on the site."
)


class CodeSnippetIndexView(IndexView):
    def get(self, request, *args, **kwargs):
        if settings.ORION_SCRIPTS_DISABLED:
            messages.warning(request, DISABLED_MESSAGE)
        return super().get(request, *args, **kwargs)


class CodeSnippetViewSet(SnippetViewSet):
    model = CodeSnippet
    icon = "code"
    menu_label = _("Code snippets")
    menu_name = "orion_code_snippets"
    menu_order = 950
    add_to_admin_menu = True
    index_view_class = CodeSnippetIndexView
    list_display = [
        "name",
        "location",
        BooleanColumn("is_active", label=_("Active")),
        "scope",
    ]
    list_filter = ["location", "is_active"]
    panels = [
        FieldPanel("name"),
        FieldPanel(
            "code", widget=forms.Textarea(attrs={"rows": 12, "spellcheck": "false"})
        ),
        FieldPanel("location"),
        FieldPanel("is_active"),
        MultiFieldPanel(
            [
                FieldPanel("scope"),
                MultipleChooserPanel(
                    "snippet_pages", chooser_field_name="page", label=_("Pages")
                ),
                FieldPanel("include_subpages"),
                FieldPanel("page_types", widget=forms.CheckboxSelectMultiple),
                FieldPanel("locales", widget=forms.CheckboxSelectMultiple),
            ],
            heading=_("Where"),
        ),
    ]


register_snippet(CodeSnippetViewSet)
