"""Typed readers for environment variables used by Orion settings.

Invalid values raise ``ImproperlyConfigured`` instead of falling back silently, so a
misconfigured deployment fails at startup rather than running with surprising values.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
FALSE_VALUES = frozenset({"0", "false", "no", "off"})


def load_env_file(path: Path) -> None:
    """Load a ``.env`` file into the environment, if it exists.

    Variables already set keep their value. Interpolation stays off: generated secret
    keys contain ``$``.
    """
    load_dotenv(path, override=False, interpolate=False)


def env_str(name: str, default: str = "") -> str:
    """Return the variable stripped of surrounding whitespace, or ``default`` when
    absent or empty."""
    raw_value = os.environ.get(name, "").strip()
    return raw_value or default


def env_bool(name: str, default: bool = False) -> bool:
    """Return the variable as a boolean, rejecting values that are not recognisable."""
    raw_value = env_str(name)
    if not raw_value:
        return default
    normalized_value = raw_value.lower()
    if normalized_value in TRUE_VALUES:
        return True
    if normalized_value in FALSE_VALUES:
        return False
    accepted_values = ", ".join(sorted(TRUE_VALUES | FALSE_VALUES))
    raise ImproperlyConfigured(
        f"{name} must be a boolean ({accepted_values}); got {raw_value!r}."
    )


def env_int(name: str, default: int) -> int:
    """Return the variable as an integer, rejecting non-numeric values."""
    raw_value = env_str(name)
    if not raw_value:
        return default
    try:
        return int(raw_value)
    except ValueError as error:
        raise ImproperlyConfigured(
            f"{name} must be an integer; got {raw_value!r}."
        ) from error


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    """Return a comma-separated variable as a list, ignoring empty items."""
    raw_value = env_str(name)
    if not raw_value:
        return list(default or [])
    return [item.strip() for item in raw_value.split(",") if item.strip()]
