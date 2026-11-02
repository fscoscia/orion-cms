import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext_lazy as _
from wagtail.documents.forms import BaseDocumentForm

from orion.core.uploads import matches_extension


class DocumentForm(BaseDocumentForm):
    """Wagtail's document form with a maximum size and the file's real type checked.

    Wagtail itself checks the extension against WAGTAILDOCS_EXTENSIONS.
    """

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if not file or "file" not in self.changed_data:
            return file
        maximum = settings.ORION_DOCUMENT_MAX_UPLOAD_MB * 1024 * 1024
        if file.size > maximum:
            raise ValidationError(
                _("The file is too large. The maximum is %(size)s.")
                % {"size": filesizeformat(maximum)},
                code="file_too_large",
            )
        extension = os.path.splitext(file.name)[1]
        if not matches_extension(file, extension):
            raise ValidationError(
                _("The file's content does not match its type (%(extension)s).")
                % {"extension": extension.lstrip(".").upper()},
                code="invalid_file_type",
            )
        return file

    def _post_clean(self):
        # Wagtail's model check would add a second, confusing error ("extension ''
        # is not allowed") for a file this form already refused.
        if self.has_error("file"):
            return
        super()._post_clean()
