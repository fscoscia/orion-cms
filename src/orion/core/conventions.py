"""Find hardcoded text, images without alt text, and incomplete translations in the
templates and translation catalogs of a project built on Orion.

A best-effort heuristic, not a full HTML or gettext parser: see design.md of
add-conventions-check for its scope and limitations.
"""

import re
import site
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.template.base import tag_re

SKIPPED_TAGS = {"script", "style"}
BLOCKTRANS_START = {"blocktrans", "blocktranslate"}
BLOCKTRANS_END = {"endblocktrans", "endblocktranslate"}
IMAGE_TAG_NAME = "responsive_image"
ALT_KWARG_RE = re.compile(r"""\balt\s*=\s*("(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|\S+)""")
FUZZY_RE = re.compile(r"^#,.*\bfuzzy\b")


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    message: str


def _site_packages_dirs() -> list[Path]:
    dirs = [Path(path).resolve() for path in site.getsitepackages()]
    if site.ENABLE_USER_SITE:
        dirs.append(Path(site.getusersitepackages()).resolve())
    return dirs


def _project_app_configs():
    """Installed apps that live in the project itself, not an installed dependency.

    An app installed normally (including Orion itself, in a project that installs
    it like any other package) lives under site-packages; only an app developed
    in place - Orion's own apps here, or a project's own apps anywhere - does not.
    Third-party apps (Django, Wagtail, django-axes...) ship their own complete
    templates and translations, which are not this project's to report on.
    """
    site_packages_dirs = _site_packages_dirs()
    for app_config in apps.get_app_configs():
        app_path = Path(app_config.path).resolve()
        if not any(app_path.is_relative_to(d) for d in site_packages_dirs):
            yield app_config


# Template discovery: each project app's own templates/, the same convention
# Django's APP_DIRS loader uses, plus the project's explicit TEMPLATES[0]["DIRS"].


def iter_template_dirs() -> list[Path]:
    dirs = {
        Path(app_config.path) / "templates" for app_config in _project_app_configs()
    }
    dirs = {d for d in dirs if d.is_dir()}
    dirs.update(Path(d) for d in settings.TEMPLATES[0]["DIRS"])
    return sorted(dirs)


def iter_template_files():
    seen = set()
    for template_dir in iter_template_dirs():
        if not template_dir.is_dir():
            continue
        for path in sorted(template_dir.rglob("*.html")):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path


# Translation catalog discovery: each project app's own locale/, plus LOCALE_PATHS.


def iter_locale_dirs() -> list[Path]:
    dirs = {Path(app_config.path) / "locale" for app_config in _project_app_configs()}
    dirs = {d for d in dirs if d.is_dir()}
    for configured in settings.LOCALE_PATHS:
        path = Path(configured)
        if path.is_dir():
            dirs.add(path)
    return sorted(dirs)


def iter_po_files():
    seen = set()
    for locale_dir in iter_locale_dirs():
        for path in sorted(locale_dir.rglob("*.po")):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield path


# Template tags: blank every {{ }}, {% %} and {# #} (and blocktrans/blocktranslate
# bodies) so only literal HTML text remains, with line numbers unchanged.


def _tag_name(chunk: str) -> str | None:
    if not chunk.startswith("{%"):
        return None
    inner = chunk[2:-2].strip()
    return inner.split()[0] if inner else None


def _mask(text: str) -> str:
    return "".join(character if character == "\n" else " " for character in text)


def _blank_regions(source: str) -> list[tuple[int, int]]:
    regions = []
    in_blocktrans = False
    blocktrans_start = 0
    for match in tag_re.finditer(source):
        start, end = match.span()
        tag_name = _tag_name(source[start:end])
        if in_blocktrans:
            if tag_name in BLOCKTRANS_END:
                regions.append((blocktrans_start, end))
                in_blocktrans = False
            continue
        if tag_name in BLOCKTRANS_START:
            in_blocktrans = True
            blocktrans_start = start
            continue
        regions.append((start, end))
    if in_blocktrans:
        # An unclosed blocktrans (a malformed template): blank to the end, defensively.
        regions.append((blocktrans_start, len(source)))
    return regions


def mask_template_tags(source: str) -> str:
    output = []
    pos = 0
    for start, end in _blank_regions(source):
        output.append(source[pos:start])
        output.append(_mask(source[start:end]))
        pos = end
    output.append(source[pos:])
    return "".join(output)


def _has_alt(tag_contents: str) -> bool:
    match = ALT_KWARG_RE.search(tag_contents)
    if match is None:
        return False
    value = match.group("dq") if match.group("dq") is not None else match.group("sq")
    if value is not None:
        return bool(value.strip())
    return (
        True  # A bare variable or filter expression: assume it resolves to something.
    )


def find_image_tags_without_alt(source: str) -> list[tuple[int, str]]:
    findings = []
    for match in tag_re.finditer(source):
        chunk = match.group(0)
        if _tag_name(chunk) != IMAGE_TAG_NAME:
            continue
        if _has_alt(chunk[2:-2].strip()):
            continue
        line = source.count("\n", 0, match.start()) + 1
        findings.append((line, f"{{% {IMAGE_TAG_NAME} %}} without alt text"))
    return findings


# HTML text and <img> scanning, on the masked (Django-tag-free) source.


class _HtmlScanner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.findings: list[tuple[int, str]] = []
        self._skip_stack: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "img" and not dict(attrs).get("alt"):
            line, _ = self.getpos()
            self.findings.append((line, "<img> without alt text"))
        if tag in SKIPPED_TAGS:
            self._skip_stack.append(tag)

    def handle_endtag(self, tag):
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()

    def handle_data(self, data):
        if self._skip_stack or not any(character.isalpha() for character in data):
            return
        line, _ = self.getpos()
        snippet = " ".join(data.split())[:60]
        self.findings.append((line, f'hardcoded text: "{snippet}"'))


def check_template(path: Path) -> list[Finding]:
    source = path.read_text(encoding="utf-8")
    findings = [
        Finding(path, line, message)
        for line, message in find_image_tags_without_alt(source)
    ]
    scanner = _HtmlScanner()
    scanner.feed(mask_template_tags(source))
    findings.extend(Finding(path, line, message) for line, message in scanner.findings)
    return findings


# Translation catalogs: a small line-based .po parser (msgid/msgstr and fuzzy only;
# plural forms are not checked, see design.md).


@dataclass(frozen=True)
class _PoEntry:
    line: int
    msgid: str
    msgstr: str
    fuzzy: bool


def _unquote(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        raw = raw[1:-1]
    return raw.replace('\\"', '"').replace("\\\\", "\\")


def parse_po_entries(text: str) -> list[_PoEntry]:
    lines = text.splitlines()
    entries = []
    index = 0
    while index < len(lines):
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            break
        fuzzy = False
        while index < len(lines) and lines[index].startswith("#"):
            if FUZZY_RE.match(lines[index]):
                fuzzy = True
            index += 1
        # msgctxt disambiguates a msgid in a particular context; its text is not
        # the message itself, so it is skipped rather than parsed as one.
        if index < len(lines) and lines[index].startswith("msgctxt"):
            index += 1
            while index < len(lines) and lines[index].startswith('"'):
                index += 1
        msgid_line = index
        msgid_parts = []
        if index < len(lines) and lines[index].startswith("msgid "):
            msgid_parts.append(_unquote(lines[index][len("msgid ") :]))
            index += 1
            while index < len(lines) and lines[index].startswith('"'):
                msgid_parts.append(_unquote(lines[index]))
                index += 1
        if index < len(lines) and lines[index].startswith("msgid_plural"):
            while index < len(lines) and (
                lines[index].startswith("msgid_plural") or lines[index].startswith('"')
            ):
                index += 1
        msgstr_parts = None
        if index < len(lines) and lines[index].startswith("msgstr "):
            msgstr_parts = [_unquote(lines[index][len("msgstr ") :])]
            index += 1
            while index < len(lines) and lines[index].startswith('"'):
                msgstr_parts.append(_unquote(lines[index]))
                index += 1
        else:
            # Plural-only entry (msgstr[0]/msgstr[1]): not checked, see design.md.
            while index < len(lines) and lines[index].startswith("msgstr["):
                index += 1
                while index < len(lines) and lines[index].startswith('"'):
                    index += 1
        msgid = "".join(msgid_parts)
        if msgid and msgstr_parts is not None:
            entries.append(
                _PoEntry(
                    line=msgid_line + 1,
                    msgid=msgid,
                    msgstr="".join(msgstr_parts),
                    fuzzy=fuzzy,
                )
            )
    return entries


def check_po_file(path: Path) -> list[Finding]:
    findings = []
    for entry in parse_po_entries(path.read_text(encoding="utf-8")):
        if entry.fuzzy:
            findings.append(
                Finding(path, entry.line, f'fuzzy translation: "{entry.msgid}"')
            )
        elif not entry.msgstr:
            findings.append(
                Finding(path, entry.line, f'missing translation: "{entry.msgid}"')
            )
    return findings


def check_project() -> list[Finding]:
    findings = []
    for template_path in iter_template_files():
        findings.extend(check_template(template_path))
    for po_path in iter_po_files():
        findings.extend(check_po_file(po_path))
    return findings
