import re
from pathlib import Path

import polib

import orion

ORION_DIR = Path(orion.__file__).parent


def test_plural_translations_have_every_form():
    """Spanish catalogs declare three plural forms (one, millions, other); a missing
    form makes Django fall back to English for that count."""
    for path in ORION_DIR.glob("*/**/es/LC_MESSAGES/*.po"):
        catalog = polib.pofile(str(path))
        forms = int(re.search(r"nplurals=(\d+)", catalog.metadata["Plural-Forms"])[1])
        for entry in catalog:
            if entry.msgid_plural:
                filled = [value for value in entry.msgstr_plural.values() if value]
                assert len(filled) == forms, f"{path}: {entry.msgid}"
