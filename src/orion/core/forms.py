"""Form fields and widgets shared by Orion's settings and blocks."""

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

LEAFLET_JS = "orion/vendor/leaflet-1.9.4/leaflet.js"
LEAFLET_CSS = "orion/vendor/leaflet-1.9.4/leaflet.css"
# Six decimals are about 10 cm, more than enough for a map marker.
LOCATION_DECIMALS = 6


def clean_location(value):
    """Return a location as ``{"lat": float, "lng": float}``, or raise ValidationError.

    Empty values return None.
    """
    if value in (None, "", {}):
        return None
    try:
        latitude = float(value["lat"])
        longitude = float(value["lng"])
    except (KeyError, TypeError, ValueError):
        raise ValidationError(
            _("Choose a location on the map."), code="invalid"
        ) from None
    if not -90 <= latitude <= 90:
        raise ValidationError(_("The latitude must be between -90 and 90."))
    if not -180 <= longitude <= 180:
        raise ValidationError(_("The longitude must be between -180 and 180."))
    return {
        "lat": round(latitude, LOCATION_DECIMALS),
        "lng": round(longitude, LOCATION_DECIMALS),
    }


class LocationWidget(forms.Widget):
    """A map to pick a location by clicking or dragging, with editable coordinates.

    The value travels as JSON in a hidden input, which Wagtail's generic widget
    adapter reads and writes inside StreamField blocks.
    """

    template_name = "orion/widgets/location_widget.html"

    class Media:
        css = {"all": [LEAFLET_CSS, "orion/admin/location.css"]}
        js = [LEAFLET_JS, "orion/admin/location.js"]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        latitude, longitude, zoom = settings.ORION_MAP_DEFAULT_CENTER
        context["default_center"] = {"lat": latitude, "lng": longitude, "zoom": zoom}
        context["tiles"] = settings.ORION_MAP_TILES
        return context


class LocationField(forms.JSONField):
    widget = LocationWidget

    def to_python(self, value):
        return clean_location(super().to_python(value))
