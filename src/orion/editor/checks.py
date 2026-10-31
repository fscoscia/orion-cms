"""System checks for the admin colors."""

from django.core.checks import Error, Tags, Warning, register

from orion.editor.colors import (
    COLOR_KEYS,
    HEX_COLOR,
    MIN_CONTRAST_WITH_WHITE,
    contrast_with_white,
    get_admin_colors,
)

INVALID_ADMIN_COLOR_ERROR_ID = "orion.E004"
LOW_CONTRAST_ADMIN_COLOR_WARNING_ID = "orion.W001"


@register(Tags.compatibility)
def check_admin_colors(app_configs, **kwargs):
    """Report admin colors that are invalid or that white text cannot be read on."""
    messages = []
    for key, value in get_admin_colors().items():
        if key not in COLOR_KEYS or not HEX_COLOR.match(str(value)):
            messages.append(
                Error(
                    f"ORION_ADMIN_COLORS has an invalid entry: {key!r}: {value!r}.",
                    hint=(
                        "Use the keys 'primary' and 'secondary' with colors like "
                        "'#1d4ed8'."
                    ),
                    id=INVALID_ADMIN_COLOR_ERROR_ID,
                )
            )
        elif contrast_with_white(value) < MIN_CONTRAST_WITH_WHITE:
            messages.append(
                Warning(
                    f"White text on the admin {key} color {value} has a contrast "
                    f"of {contrast_with_white(value):.1f}:1.",
                    hint=f"Use a darker color, with at least "
                    f"{MIN_CONTRAST_WITH_WHITE}:1 against white.",
                    id=LOW_CONTRAST_ADMIN_COLOR_WARNING_ID,
                )
            )
    return messages
