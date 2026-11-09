"""Console entry point: ``orion-start <project_name> [destination]``.

Wraps Django's native ``startproject`` with Orion's packaged project template, the
same way ``wagtail start`` wraps it with Wagtail's own template.
"""

import sys
from pathlib import Path

from django.core.management import ManagementUtility

import orion

TEMPLATE_DIR = Path(__file__).resolve().parent / "project_template"
STATIC_SRC_DIR = Path(__file__).resolve().parent / "core" / "static_src"
VERSION_PLACEHOLDER = "__ORION_VERSION__"
STATIC_SRC_PLACEHOLDER = "__ORION_STATIC_SRC__"
PROJECT_NAME_PLACEHOLDER = "__PROJECT_NAME__"
# Files of the template that name the project, written as plain text (Django would
# render them as templates and choke on the template tags they document).
PROJECT_NAME_FILES = ("AGENTS.md", "CLAUDE.md")


def main():
    args = sys.argv[1:]
    positional = [arg for arg in args if not arg.startswith("-")]
    if not positional:
        print("Usage: orion-start <project_name> [destination]")  # noqa: T201
        sys.exit(1)
    project_name = positional[0]
    destination = (
        Path(positional[1]).resolve()
        if len(positional) > 1
        else Path.cwd() / project_name
    )

    utility = ManagementUtility(
        ["django-admin", "startproject", f"--template={TEMPLATE_DIR}", *args]
    )
    utility.execute()

    pipfile = destination / "Pipfile"
    if pipfile.exists():
        pipfile.write_text(
            pipfile.read_text().replace(VERSION_PLACEHOLDER, orion.__version__)
        )

    for filename in PROJECT_NAME_FILES:
        instructions = destination / filename
        if instructions.exists():
            instructions.write_text(
                instructions.read_text().replace(PROJECT_NAME_PLACEHOLDER, project_name)
            )

    project_css = destination / "static_src" / "project.css"
    if project_css.exists():
        project_css.write_text(
            project_css.read_text().replace(STATIC_SRC_PLACEHOLDER, str(STATIC_SRC_DIR))
        )
        # STATICFILES_DIRS source for the compiled CSS; django-tailwind-cli writes
        # into it but never creates it, and an empty directory can't ship in the
        # template (nothing to track, and it would match the project's own
        # .gitignore if it did).
        (destination / "assets").mkdir(exist_ok=True)


if __name__ == "__main__":
    main()
