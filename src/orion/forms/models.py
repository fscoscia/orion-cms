"""Forms that editors build: the page, its fields and its submissions."""

import logging
import os
import uuid

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import EmailMessage
from django.db import models
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import get_valid_filename
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    InlinePanel,
    MultiFieldPanel,
    ObjectList,
    TabbedInterface,
)
from wagtail.contrib.forms.forms import WagtailAdminFormPageForm
from wagtail.contrib.forms.models import (
    AbstractEmailForm,
    AbstractFormField,
    AbstractFormSubmission,
)
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index

from orion.forms.builder import (
    CONSENT_FIELD,
    SYSTEM_FIELDS,
    OrionFormBuilder,
)
from orion.forms.storage import get_private_storage
from orion.pages.models import DesktopPreviewMixin
from orion.seo.models import SeoMixin

logger = logging.getLogger(__name__)

FIELD_TYPE_CHOICES = [
    ("singleline", _("Single line text")),
    ("multiline", _("Multi-line text")),
    ("email", _("Email")),
    ("phone", _("Phone")),
    ("number", _("Number")),
    ("dropdown", _("Drop down")),
    ("radio", _("Radio buttons")),
    ("checkboxes", _("Checkboxes")),
    ("checkbox", _("Checkbox")),
    ("date", _("Date")),
    ("file", _("File")),
]


class FormField(AbstractFormField):
    page = ParentalKey(
        "orion_forms.FormPage", on_delete=models.CASCADE, related_name="form_fields"
    )
    field_type = models.CharField(
        _("field type"), max_length=16, choices=FIELD_TYPE_CHOICES
    )


class SubmissionStatus(models.TextChoices):
    NEW = "new", _("New")
    READ = "read", _("Read")
    ANSWERED = "answered", _("Answered")


class FormSubmission(AbstractFormSubmission):
    # Its own reverse name: Wagtail's FormSubmission already uses the default one.
    page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="orion_form_submissions"
    )
    consent_at = models.DateTimeField(_("consent given at"), null=True, blank=True)
    status = models.CharField(
        _("status"),
        max_length=10,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.NEW,
        db_index=True,
    )

    def attachments(self):
        """The submission's attachments as ``(field name, {"name", "path"})``."""
        return [
            (name, value)
            for name, value in self.form_data.items()
            if isinstance(value, dict) and "path" in value
        ]

    def get_data(self):
        """The submitted values, with the status; attachments as a download link."""
        data = {**super().get_data(), "status": self.get_status_display()}
        for name, value in data.items():
            if value is None:
                # An optional field left empty, such as an attachment.
                data[name] = ""
            elif isinstance(value, dict) and "path" in value:
                data[name] = format_html(
                    '<a href="{}">{}</a>',
                    reverse("orion_form_attachment", args=[self.pk, name]),
                    value["name"],
                )
        return data


class SubmissionNote(models.Model):
    """An internal note about a submission, never shown to the visitor."""

    submission = models.ForeignKey(
        FormSubmission,
        on_delete=models.CASCADE,
        related_name="notes",
        verbose_name=_("submission"),
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("author"),
    )
    text = models.TextField(_("note"), max_length=2000)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = _("note")
        verbose_name_plural = _("notes")

    def __str__(self):
        return self.text[:50]


class FormPageForm(WagtailAdminFormPageForm):
    """Applies the project's limits on the fields editors add."""

    def clean(self):
        cleaned_data = super().clean()
        fields = [
            form
            for form in self.formsets["form_fields"].forms
            if form.is_valid() and not form.cleaned_data.get("DELETE")
        ]
        maximum = settings.ORION_FORMS_MAX_FIELDS
        if len(fields) > maximum:
            self.add_error(
                None,
                _("A form can have at most %(maximum)s fields.") % {"maximum": maximum},
            )
        allowed = settings.ORION_FORMS_FIELD_TYPES
        if allowed is not None:
            for form in fields:
                if form.cleaned_data.get("field_type") not in allowed:
                    form.add_error("field_type", _("This field type is not allowed."))
        return cleaned_data


class FormPage(SeoMixin, DesktopPreviewMixin, AbstractEmailForm):
    intro = RichTextField(
        _("introduction"), blank=True, features=["bold", "italic", "link"]
    )
    thank_you_text = RichTextField(
        _("thank-you text"),
        blank=True,
        features=["bold", "italic", "link"],
        help_text=_("Shown after sending, unless a page is chosen below."),
    )
    thank_you_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name=_("page after sending"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Optional: visitors go to this page after sending."),
    )
    from_name = models.CharField(
        _("sender name"),
        max_length=100,
        blank=True,
        help_text=_("For example, the site name."),
    )

    search_fields = [*SeoMixin.search_fields, index.SearchField("intro")]
    form_builder = OrionFormBuilder
    base_form_class = FormPageForm
    parent_page_types = ["orion_pages.HomePage", "orion_pages.ContentPage"]
    subpage_types = []
    template = "orion/forms/form_page.html"
    landing_page_template = "orion/forms/form_page_landing.html"

    content_panels = [
        *Page.content_panels,
        FieldPanel("intro"),
        InlinePanel("form_fields", label=_("Fields")),
    ]
    after_panels = [
        FieldPanel("thank_you_text"),
        FieldPanel("thank_you_page"),
    ]
    email_panels = [
        MultiFieldPanel(
            [
                FieldPanel("to_address"),
                FieldPanel("subject"),
                FieldRowPanel([FieldPanel("from_name"), FieldPanel("from_address")]),
            ],
            heading=_("Email notice"),
        )
    ]
    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading=_("Content")),
            ObjectList(after_panels, heading=_("After sending")),
            ObjectList(email_panels, heading=_("Email")),
            ObjectList(SeoMixin.promote_panels, heading=_("Promote")),
            ObjectList(Page.settings_panels, heading=_("Settings")),
        ]
    )

    class Meta:
        verbose_name = _("form")
        verbose_name_plural = _("forms")

    def get_submission_class(self):
        return FormSubmission

    def get_submissions_list_view_class(self):
        from orion.forms.submissions import OrionSubmissionsListView

        return OrionSubmissionsListView

    def get_data_fields(self):
        submit_time, *fields = super().get_data_fields()
        return [submit_time, ("status", _("Status")), *fields]

    def get_form_parameters(self):
        return {"privacy_url": get_privacy_url()}

    def serve(self, request, *args, **kwargs):
        if request.method == "POST":
            form = self.get_form(
                request.POST, request.FILES, page=self, user=request.user
            )
            if form.is_valid():
                if is_rate_limited(self, request):
                    form.add_error(
                        None,
                        _("Too many submissions. Wait a few minutes and try again."),
                    )
                else:
                    submission = self.process_form_submission(form)
                    return self.render_landing_page(request, submission)
        else:
            form = self.get_form(page=self, user=request.user)
        context = self.get_context(request)
        context["form"] = form
        return TemplateResponse(request, self.get_template(request), context)

    def process_form_submission(self, form):
        data = {
            name: value
            for name, value in form.cleaned_data.items()
            if name not in SYSTEM_FIELDS
        }
        for name, value in data.items():
            if isinstance(value, UploadedFile):
                data[name] = save_attachment(self, value)
        submission = self.get_submission_class().objects.create(
            form_data=data,
            page=self,
            consent_at=timezone.now() if form.cleaned_data.get(CONSENT_FIELD) else None,
        )
        if self.to_address:
            self.send_mail(form, submission)
        return submission

    def render_landing_page(self, request, form_submission=None, *args, **kwargs):
        target = self.thank_you_page
        if target is not None and target.live:
            response = HttpResponseRedirect(target.localized.url)
            # See Other: the browser asks for the page with GET, not resending.
            response.status_code = 303
            return response
        return super().render_landing_page(request, form_submission, *args, **kwargs)

    def get_from_email(self):
        address = self.from_address or settings.DEFAULT_FROM_EMAIL
        return f'"{self.from_name}" <{address}>' if self.from_name else address

    def get_recipients(self):
        return [address.strip() for address in self.to_address.split(",") if address]

    def send_mail(self, form, submission=None):
        # Replying writes to the first email the visitor left.
        reply_to = next(
            (
                form.cleaned_data[field.clean_name]
                for field in self.get_form_fields()
                if field.field_type == "email"
                and form.cleaned_data.get(field.clean_name)
            ),
            None,
        )
        message = EmailMessage(
            subject=self.subject or self.title,
            body=self.render_email(form),
            from_email=self.get_from_email(),
            to=self.get_recipients(),
            reply_to=[reply_to] if reply_to else None,
        )
        try:
            message.send()
        except Exception:
            # The submission is already saved: a mail error must not lose it.
            logger.exception("Could not email the submission of form %s", self.pk)

    def render_email(self, form):
        submissions_url = settings.WAGTAILADMIN_BASE_URL.rstrip("/") + reverse(
            "wagtailforms:list_submissions", args=[self.pk]
        )
        lines = []
        for field in form.editor_fields:
            value = form.cleaned_data.get(field.name)
            if isinstance(value, UploadedFile):
                value = gettext("%(name)s (download it from %(url)s)") % {
                    "name": value.name,
                    "url": submissions_url,
                }
            elif isinstance(value, list):
                value = ", ".join(value)
            elif value is None:
                value = ""
            lines.append(f"{field.label}: {value}")
        return "\n".join(lines)


def get_privacy_url():
    # Imported here: site settings load after page models.
    from orion.site_data.models import SiteSettings

    page = SiteSettings.load().privacy_page
    if page is None:
        return None
    translated = page.localized
    return translated.url if translated.live else None


def is_rate_limited(page, request):
    """Count a submission from the visitor's address; True past the limit."""
    count, seconds = settings.ORION_FORMS_RATE_LIMIT
    key = f"orion:form-rate:{page.pk}:{request.META.get('REMOTE_ADDR', '')}"
    if cache.add(key, 1, seconds):
        return False
    try:
        return cache.incr(key) > count
    except ValueError:
        # The window ended between add and incr.
        cache.add(key, 1, seconds)
        return False


def save_attachment(page, uploaded_file):
    """Store an uploaded file privately and return its reference for form_data."""
    name = get_valid_filename(os.path.basename(uploaded_file.name)) or "file"
    path = get_private_storage().save(
        f"forms/{page.pk}/{uuid.uuid4().hex}/{name}", uploaded_file
    )
    return {"name": uploaded_file.name, "path": path}


def sample_form():
    """An unbound example form, for the block preview in the editor."""
    fields = [
        FormField(label=label, field_type=field_type, required=required)
        for label, field_type, required in (
            (_("Name"), "singleline", True),
            (_("Email"), "email", True),
            (_("Message"), "multiline", True),
        )
    ]
    return OrionFormBuilder(fields).get_form_class()(page=None)
