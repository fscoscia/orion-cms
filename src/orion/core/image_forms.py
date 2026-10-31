from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail.images.forms import BaseImageForm

from orion.core.svg import InvalidSVGError, clean_svg


class ImageForm(BaseImageForm):
    """Wagtail's image form, rejecting SVG files that cannot be cleaned safely."""

    def clean_file(self):
        file = self.cleaned_data.get("file")
        if file and file.name.lower().endswith(".svg") and "file" in self.changed_data:
            file.seek(0)
            try:
                clean_svg(file.read())
            except InvalidSVGError:
                raise ValidationError(
                    _("The file is not a valid SVG image."), code="invalid_svg"
                ) from None
            finally:
                file.seek(0)
        return file
