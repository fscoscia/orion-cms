"""The project's admin colors (ORION_ADMIN_COLORS), as Wagtail's admin CSS variables."""

import colorsys
import re

from django.conf import settings

COLOR_KEYS = ("primary", "secondary")
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
# WCAG AA for normal text: the admin shows white text on these colors.
MIN_CONTRAST_WITH_WHITE = 4.5


def get_admin_colors():
    return getattr(settings, "ORION_ADMIN_COLORS", None) or {}


def _channels(hex_color):
    return [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]


def hex_to_hsl(hex_color):
    """Return ``(hue in degrees, saturation %, lightness %)``, rounded."""
    red, green, blue = _channels(hex_color)
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    return round(hue * 360), round(saturation * 100), round(lightness * 100)


def contrast_with_white(hex_color):
    """WCAG contrast ratio between white and the color."""

    def linear(channel):
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in _channels(hex_color))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return 1.05 / (luminance + 0.05)


def admin_colors_css():
    """CSS that sets Wagtail's admin color variables from ORION_ADMIN_COLORS."""
    declarations = []
    for key, hex_color in get_admin_colors().items():
        if key not in COLOR_KEYS or not HEX_COLOR.match(str(hex_color)):
            continue
        hue, saturation, lightness = hex_to_hsl(hex_color)
        declarations += [
            f"  --w-color-{key}-hue: {hue};",
            f"  --w-color-{key}-saturation: {saturation}%;",
            f"  --w-color-{key}-lightness: {lightness}%;",
        ]
    if not declarations:
        return ""
    return ":root {\n" + "\n".join(declarations) + "\n}\n"
