"""Third-party code (analytics, pixels, chats) pasted from the admin into pages."""

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.models import Orderable, RevisionMixin, get_page_models


class Location(models.TextChoices):
    HEAD = "head", _("Inside <head>")
    BODY_START = "body_start", _("Start of <body>")
    BODY_END = "body_end", _("End of <body>")


class Scope(models.TextChoices):
    SITE = "site", _("The whole site")
    PAGES = "pages", _("Chosen pages")
    PAGE_TYPES = "page_types", _("Chosen page types")


def page_content_types():
    return models.Q(
        pk__in=[
            ContentType.objects.get_for_model(model).pk
            for model in get_page_models()
            if not model._meta.abstract
        ]
    )


class CodeSnippetForm(WagtailAdminModelForm):
    """Requires the pages or page types that the chosen scope needs."""

    def clean(self):
        cleaned_data = super().clean()
        scope = cleaned_data.get("scope")
        pages = [
            form
            for form in self.formsets["snippet_pages"].forms
            if form.is_valid()
            and form.cleaned_data.get("page")
            and not form.cleaned_data.get("DELETE")
        ]
        if scope == Scope.PAGES and not pages:
            self.add_error("scope", _("Choose at least one page."))
        if scope == Scope.PAGE_TYPES and not cleaned_data.get("page_types"):
            self.add_error("page_types", _("Choose at least one page type."))
        return cleaned_data


class CodeSnippet(RevisionMixin, ClusterableModel):
    name = models.CharField(_("name"), max_length=100)
    code = models.TextField(
        _("code"),
        help_text=_(
            "Pasted as is into the pages: it runs in every visitor's browser. Paste "
            "only code from a trusted service."
        ),
    )
    location = models.CharField(
        _("location"), max_length=10, choices=Location.choices, default=Location.HEAD
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_("Turn off to stop loading it without deleting it."),
    )
    scope = models.CharField(
        _("where"), max_length=10, choices=Scope.choices, default=Scope.SITE
    )
    include_subpages = models.BooleanField(_("include their subpages"), default=True)
    page_types = ParentalManyToManyField(
        ContentType,
        verbose_name=_("page types"),
        blank=True,
        related_name="+",
        limit_choices_to=page_content_types,
    )
    locales = ParentalManyToManyField(
        "wagtailcore.Locale",
        verbose_name=_("languages"),
        blank=True,
        related_name="+",
        help_text=_("Leave empty for every language."),
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    base_form_class = CodeSnippetForm

    class Meta:
        ordering = ["created_at", "pk"]
        verbose_name = _("code snippet")
        verbose_name_plural = _("code snippets")

    def __str__(self):
        return self.name


class CodeSnippetPage(Orderable):
    """A page a snippet applies to, when its scope is "Chosen pages"."""

    snippet = ParentalKey(
        CodeSnippet, on_delete=models.CASCADE, related_name="snippet_pages"
    )
    page = models.ForeignKey(
        "wagtailcore.Page",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("page"),
    )

    class Meta(Orderable.Meta):
        verbose_name = _("page")
        verbose_name_plural = _("pages")
