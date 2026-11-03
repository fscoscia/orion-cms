"""Console entry point: ``orion-start <project_name> [destination]``.

Wraps Django's native ``startproject`` with Orion's packaged project template, the
same way ``wagtail start`` wraps it with Wagtail's own template.
"""

import sys
from pathlib import Path

from django.core.management import ManagementUtility

import orion

TEMPLATE_DIR = Path(__file__).resolve().parent / "project_template"
VERSION_PLACEHOLDER = "__ORION_VERSION__"


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


if __name__ == "__main__":
    main()
