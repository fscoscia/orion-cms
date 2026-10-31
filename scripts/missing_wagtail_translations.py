"""List the Wagtail phrases that no installed catalog translates, as .po entries.

After upgrading Wagtail, run it from the repository root through Django's shell and add
the output, translated, to src/orion/editor/wagtail_locale/es/LC_MESSAGES/<domain>.po:

    pipenv run manage shell < scripts/missing_wagtail_translations.py
"""

from orion.editor.translations import missing_wagtail_translations

for (domain, msgid), plural in sorted(missing_wagtail_translations("es").items()):
    print(f"# {domain}.po")
    print(f'msgid "{msgid}"')
    if plural:
        print(f'msgid_plural "{plural}"')
        print('msgstr[0] ""\nmsgstr[1] ""\nmsgstr[2] ""\n')
    else:
        print('msgstr ""\n')
