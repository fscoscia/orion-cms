"""The form builder: Wagtail's, plus phone and file fields, and the fields Orion adds
to every form (a trap for bots, the time it was shown and the consent)."""

import os
import time

from django import forms
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from wagtail.contrib.forms.forms import BaseForm, FormBuilder

from orion.core.uploads import matches_extension

TRAP_FIELD = "website"
RENDERED_AT_FIELD = "rendered_at"
CONSENT_FIELD = "consent"
SYSTEM_FIELDS = (TRAP_FIELD, RENDERED_AT_FIELD, CONSENT_FIELD)
RENDERED_AT_MAX_AGE = 60 * 60 * 24
SIGNER_SALT = "orion.forms.rendered_at"

PHONE_VALIDATOR = RegexValidator(
    r"^[0-9+()\-.\s]{6,30}$", _("Enter a valid phone number.")
)
REJECTED_MESSAGE = _("The form could not be sent. Wait a few seconds and try again.")


def validate_attachment(file):
    extension = os.path.splitext(file.name)[1].lower().lstrip(".")
    allowed = settings.ORION_FORMS_UPLOAD_EXTENSIONS
    # A program renamed to .pdf is refused like any type that is not allowed.
    if extension not in allowed or not matches_extension(file, extension):
        raise ValidationError(
            _("Files of this type are not accepted. Allowed: %(types)s.")
            % {"types": ", ".join(allowed)}
        )
    if file.size > settings.ORION_FORMS_UPLOAD_MAX_MB * 1024 * 1024:
        raise ValidationError(
            _("The file is too large. The maximum is %(size)s.")
            % {"size": filesizeformat(settings.ORION_FORMS_UPLOAD_MAX_MB * 1024 * 1024)}
        )


class OrionBaseForm(BaseForm):
    """Adds the trap, the signed time the form was shown and the consent."""

    def __init__(self, *args, privacy_url=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.privacy_url = privacy_url
        self.fields[TRAP_FIELD] = forms.CharField(
            required=False,
            label=_("Leave this field empty"),
            widget=forms.TextInput(attrs={"autocomplete": "off", "tabindex": "-1"}),
        )
        self.fields[RENDERED_AT_FIELD] = forms.CharField(
            required=False,
            widget=forms.HiddenInput,
            initial=signing.dumps(
                {"page": self.page.pk if self.page else None, "at": time.time()},
                salt=SIGNER_SALT,
            ),
        )
        self.fields[CONSENT_FIELD] = forms.BooleanField(
            required=True,
            label=_("I accept the privacy policy."),
            error_messages={"required": _("Accept the privacy policy to send.")},
        )

    @property
    def editor_fields(self):
        return [field for field in self if field.name not in SYSTEM_FIELDS]

    def __getitem__(self, name):
        """Each field announces its help text and errors to screen readers."""
        bound_field = super().__getitem__(name)
        described_by = []
        if bound_field.help_text:
            described_by.append(f"{bound_field.auto_id}_help")
        if self.is_bound and bound_field.errors:
            described_by.append(f"{bound_field.auto_id}_errors")
            bound_field.field.widget.attrs["aria-invalid"] = "true"
        if described_by:
            bound_field.field.widget.attrs["aria-describedby"] = " ".join(described_by)
        return bound_field

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get(TRAP_FIELD) or not self._was_shown_long_enough():
            raise ValidationError(REJECTED_MESSAGE, code="rejected")
        return cleaned_data

    def _was_shown_long_enough(self):
        """The signed time the form was shown: for this page, at least
        ORION_FORMS_MIN_SECONDS ago and at most a day ago."""
        try:
            shown = signing.loads(
                self.data.get(RENDERED_AT_FIELD, ""),
                salt=SIGNER_SALT,
                max_age=RENDERED_AT_MAX_AGE,
            )
        except signing.BadSignature:
            return False
        if self.page is None or shown.get("page") != self.page.pk:
            return False
        return time.time() - shown.get("at", 0) >= settings.ORION_FORMS_MIN_SECONDS


class OrionFormBuilder(FormBuilder):
    def create_phone_field(self, field, options):
        options["max_length"] = 30
        options["validators"] = [PHONE_VALIDATOR]
        return forms.CharField(
            widget=forms.TextInput(attrs={"type": "tel", "autocomplete": "tel"}),
            **options,
        )

    def create_file_field(self, field, options):
        options.pop("initial", None)
        accept = ",".join(f".{ext}" for ext in settings.ORION_FORMS_UPLOAD_EXTENSIONS)
        return forms.FileField(
            validators=[validate_attachment],
            widget=forms.ClearableFileInput(attrs={"accept": accept}),
            **options,
        )

    def get_form_class(self):
        return type("OrionForm", (OrionBaseForm,), self.formfields)
