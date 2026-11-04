import io
import textwrap

from django.core.management import call_command

from orion.core.conventions import (
    Finding,
    check_po_file,
    check_project,
    check_template,
    find_image_tags_without_alt,
    iter_locale_dirs,
    iter_po_files,
    iter_template_dirs,
    iter_template_files,
    mask_template_tags,
    parse_po_entries,
)


def _dedent(text):
    return textwrap.dedent(text).lstrip("\n")


class TestMaskTemplateTags:
    def test_blanks_variables_and_tags_keeping_line_numbers(self):
        source = _dedent(
            """\
            {% load i18n %}
            <p>{{ value }}</p>
            """
        )

        masked = mask_template_tags(source)

        assert masked.splitlines()[0].strip() == ""
        assert "{{" not in masked and "{%" not in masked
        assert masked.count("\n") == source.count("\n")

    def test_blanks_blocktrans_body_entirely(self):
        source = _dedent(
            """\
            {% blocktrans %}Hello {{ name }}{% endblocktrans %}
            <p>Visible</p>
            """
        )

        masked = mask_template_tags(source)

        assert "Hello" not in masked
        assert "Visible" in masked


class TestFindImageTagsWithoutAlt:
    def test_missing_alt_is_reported(self):
        source = '{% responsive_image value.image "hero" %}'

        findings = find_image_tags_without_alt(source)

        assert len(findings) == 1
        assert findings[0][0] == 1

    def test_empty_alt_literal_is_reported(self):
        source = '{% responsive_image value.image "hero" alt="" %}'

        assert len(find_image_tags_without_alt(source)) == 1

    def test_variable_alt_is_not_reported(self):
        source = (
            '{% responsive_image value.image "hero" '
            "alt=value.image.contextual_alt_text %}"
        )

        assert find_image_tags_without_alt(source) == []

    def test_literal_alt_is_not_reported(self):
        source = '{% responsive_image value.image "hero" alt="A photo" %}'

        assert find_image_tags_without_alt(source) == []


class TestCheckTemplate:
    def test_hardcoded_text_is_reported_with_its_line(self, tmp_path):
        template = tmp_path / "sample.html"
        template.write_text(
            _dedent(
                """\
                {% load i18n %}
                <p>Hello world</p>
                """
            )
        )

        findings = check_template(template)

        messages = [f.message for f in findings]
        assert any("Hello world" in message for message in messages)
        matching = next(f for f in findings if "Hello world" in f.message)
        assert matching.line == 2

    def test_translated_text_is_not_reported(self, tmp_path):
        template = tmp_path / "sample.html"
        template.write_text(
            "{% load i18n %}\n<p>{% blocktrans %}Hello world{% endblocktrans %}</p>\n"
        )

        findings = check_template(template)

        assert not any("Hello world" in f.message for f in findings)

    def test_text_inside_script_is_not_reported(self, tmp_path):
        template = tmp_path / "sample.html"
        template.write_text("<script>var hello = 'world';</script>\n")

        findings = check_template(template)

        assert findings == []

    def test_img_without_alt_is_reported(self, tmp_path):
        template = tmp_path / "sample.html"
        template.write_text('<img src="{{ value.url }}">\n')

        findings = check_template(template)

        assert any("without alt text" in f.message for f in findings)

    def test_img_with_alt_is_not_reported(self, tmp_path):
        template = tmp_path / "sample.html"
        template.write_text('<img src="{{ value.url }}" alt="A photo">\n')

        findings = check_template(template)

        assert findings == []


class TestParsePoEntries:
    def test_empty_msgstr_is_reported(self):
        text = _dedent(
            """\
            msgid ""
            msgstr ""

            #: templates/sample.html:1
            msgid "Hello"
            msgstr ""
            """
        )

        entries = parse_po_entries(text)

        assert len(entries) == 1
        assert entries[0].msgid == "Hello"
        assert entries[0].msgstr == ""
        assert entries[0].fuzzy is False

    def test_fuzzy_entry_is_flagged(self):
        text = _dedent(
            """\
            msgid ""
            msgstr ""

            #, fuzzy
            msgid "Hello"
            msgstr "Algo"
            """
        )

        entries = parse_po_entries(text)

        assert len(entries) == 1
        assert entries[0].fuzzy is True

    def test_complete_entry_is_not_flagged(self):
        text = _dedent(
            """\
            msgid ""
            msgstr ""

            msgid "Hello"
            msgstr "Hola"
            """
        )

        entries = parse_po_entries(text)

        assert len(entries) == 1
        assert entries[0].msgstr == "Hola"
        assert entries[0].fuzzy is False

    def test_header_is_not_an_entry(self):
        text = _dedent(
            """\
            msgid ""
            msgstr ""
            "Content-Type: text/plain; charset=UTF-8\\n"
            """
        )

        assert parse_po_entries(text) == []

    def test_multiline_msgid_and_msgstr(self):
        text = _dedent(
            """\
            msgid ""
            msgstr ""

            msgid ""
            "Part one "
            "part two"
            msgstr ""
            "Parte uno "
            "parte dos"
            """
        )

        entries = parse_po_entries(text)

        assert len(entries) == 1
        assert entries[0].msgid == "Part one part two"
        assert entries[0].msgstr == "Parte uno parte dos"


class TestCheckPoFile:
    def test_reports_missing_and_fuzzy_entries(self, tmp_path):
        po_path = tmp_path / "django.po"
        po_path.write_text(
            _dedent(
                """\
                msgid ""
                msgstr ""

                msgid "Missing"
                msgstr ""

                #, fuzzy
                msgid "Fuzzy"
                msgstr "Algo"

                msgid "Complete"
                msgstr "Completo"
                """
            )
        )

        findings = check_po_file(po_path)

        messages = [f.message for f in findings]
        assert any("Missing" in m and "missing translation" in m for m in messages)
        assert any("Fuzzy" in m and "fuzzy translation" in m for m in messages)
        assert not any("Complete" in m for m in messages)


class TestDiscovery:
    def test_iter_template_dirs_includes_project_dirs(self, settings):
        dirs = iter_template_dirs()

        assert any(str(d).endswith("templates") for d in dirs)

    def test_iter_template_files_does_not_duplicate_shared_dirs(self, settings):
        files = list(iter_template_files())

        assert len(files) == len(set(files))

    def test_iter_locale_dirs_includes_app_locale_dirs(self):
        dirs = iter_locale_dirs()

        assert any(d.name == "locale" for d in dirs)

    def test_iter_po_files_does_not_duplicate(self):
        files = list(iter_po_files())

        assert len(files) == len(set(files))
        assert files  # Orion's own apps ship .po files.


class TestCheckProject:
    def test_runs_over_the_real_project_without_crashing(self):
        findings = check_project()

        assert isinstance(findings, list)
        assert all(isinstance(f, Finding) for f in findings)


class TestCommand:
    def test_reports_no_findings(self, monkeypatch):
        monkeypatch.setattr(
            "orion.core.management.commands.orion_check_conventions.check_project",
            lambda: [],
        )
        out = io.StringIO()

        call_command("orion_check_conventions", stdout=out)

        assert "No findings" in out.getvalue()

    def test_lists_findings_and_exits_cleanly(self, tmp_path, monkeypatch):
        fake_findings = [
            Finding(tmp_path / "a.html", 3, 'hardcoded text: "Hi"'),
            Finding(tmp_path / "b.html", 5, "<img> without alt text"),
        ]
        monkeypatch.setattr(
            "orion.core.management.commands.orion_check_conventions.check_project",
            lambda: fake_findings,
        )
        out = io.StringIO()

        call_command("orion_check_conventions", stdout=out)

        output = out.getvalue()
        assert "hardcoded text" in output
        assert "without alt text" in output
        assert "Findings: 2" in output

    def test_never_fails(self):
        # No mocking: a real run against this project's own templates and catalogs
        # (known to have findings, see design.md) must still exit 0.
        call_command("orion_check_conventions", stdout=io.StringIO())
