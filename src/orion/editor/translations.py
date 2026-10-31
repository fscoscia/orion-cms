"""Find Wagtail and wagtail-localize phrases that no installed catalog translates.

Wagtail's catalogs omit untranslated phrases, so its English source catalogs are
compared with what gettext can find at runtime: the catalogs of Django and of every
installed app, plus Orion's own catalog in ``wagtail_locale`` (``LOCALE_PATHS``).
"""

import re
from pathlib import Path

import django
from django.apps import apps

ORION_WAGTAIL_LOCALE = Path(__file__).parent / "wagtail_locale"
SOURCE_PACKAGES = ("wagtail", "wagtail_localize")
_ENTRY = re.compile(
    r'^msgid ((?:"(?:[^"\\]|\\.)*"\n?)+)(?:msgid_plural ((?:"(?:[^"\\]|\\.)*"\n?)+))?',
    re.M,
)
_MSGSTR = re.compile(r'^msgstr(?:\[\d\])? ((?:"(?:[^"\\]|\\.)*"\n?)+)', re.M)
_STRING = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _join(block):
    return "".join(_STRING.findall(block)) if block else None


def read_catalog(path, translated_only=False):
    """Return ``{msgid: msgid_plural}`` of a .po file, skipping obsolete entries."""
    entries = {}
    if not path.exists():
        return entries
    for entry in path.read_text(encoding="utf-8").split("\n\n"):
        body = "\n".join(
            line for line in entry.splitlines() if not line.startswith("#")
        )
        match = _ENTRY.search(body)
        msgid = _join(match.group(1)) if match else None
        if not msgid:
            continue
        if translated_only and not any(_join(value) for value in _MSGSTR.findall(body)):
            continue
        entries[msgid] = _join(match.group(2))
    return entries


def _installed_locale_dirs():
    yield Path(django.__file__).parent / "conf" / "locale"
    for app_config in apps.get_app_configs():
        yield Path(app_config.path) / "locale"


def installed_translations(domain, language):
    """Phrases that Django and the installed apps translate, without Orion's catalog."""
    translated = {}
    for locale_dir in _installed_locale_dirs():
        catalog = locale_dir / language / "LC_MESSAGES" / f"{domain}.po"
        translated |= read_catalog(catalog, translated_only=True)
    return translated


def orion_translations(domain, language):
    catalog = ORION_WAGTAIL_LOCALE / language / "LC_MESSAGES" / f"{domain}.po"
    return read_catalog(catalog, translated_only=True)


def _source_catalogs():
    for app_config in apps.get_app_configs():
        if app_config.name.split(".")[0] in SOURCE_PACKAGES:
            yield from sorted(
                (Path(app_config.path) / "locale" / "en" / "LC_MESSAGES").glob("*.po")
            )


def missing_wagtail_translations(language="es"):
    """Return ``{(domain, msgid): msgid_plural}`` for the phrases nobody translates."""
    missing = {}
    for source in _source_catalogs():
        domain = source.stem
        translated = installed_translations(domain, language) | orion_translations(
            domain, language
        )
        for msgid, plural in read_catalog(source).items():
            if msgid not in translated:
                missing[(domain, msgid)] = plural
    return missing


def redundant_orion_translations(language="es", domains=("django", "djangojs")):
    """Phrases in Orion's catalog that an installed catalog already translates."""
    return {
        (domain, msgid)
        for domain in domains
        for msgid in orion_translations(domain, language)
        if msgid in installed_translations(domain, language)
    }
