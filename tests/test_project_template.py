import os
import subprocess
import sys

import pytest

from orion import __version__ as orion_version
from orion.bin import main as orion_start


def _run_orion_start(monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["orion-start", *args])
    orion_start()


class TestOrionStart:
    def test_scaffolds_a_new_project(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        assert (destination / "manage.py").is_file()
        assert (destination / "mysite" / "settings.py").is_file()
        assert (destination / "mysite" / "urls.py").is_file()
        assert (destination / "mysite" / "wsgi.py").is_file()
        assert (destination / "home" / "apps.py").is_file()
        assert (destination / "templates" / "README.md").is_file()
        assert (destination / ".env.example").is_file()
        assert (destination / "Pipfile").is_file()

    def test_settings_connect_to_orion(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        settings_content = (destination / "mysite" / "settings.py").read_text()
        assert "from orion.settings.base import *" in settings_content
        assert 'ROOT_URLCONF = "mysite.urls"' in settings_content
        assert 'WSGI_APPLICATION = "mysite.wsgi.application"' in settings_content
        assert "MEDIA_ROOT = BASE_DIR / " in settings_content
        assert 'TEMPLATES[0]["DIRS"]' in settings_content

    def test_pipfile_pins_the_installed_version(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        pipfile_content = (destination / "Pipfile").read_text()
        assert "__ORION_VERSION__" not in pipfile_content
        assert f'ref = "v{orion_version}"' in pipfile_content

    def test_refuses_to_overwrite_an_existing_project(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()
        (destination / "manage.py").write_text("# already here")

        with pytest.raises(SystemExit):
            _run_orion_start(monkeypatch, "mysite", str(destination))

        # The existing file is untouched; nothing else was written alongside it.
        assert (destination / "manage.py").read_text() == "# already here"
        assert not (destination / "mysite").exists()

    def test_generated_project_passes_manage_check(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()
        _run_orion_start(monkeypatch, "mysite", str(destination))

        env = {**os.environ, "DEBUG": "true", "DATABASE_URL": "postgres:///orion"}
        env.pop("DJANGO_SETTINGS_MODULE", None)
        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=destination,
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert "System check identified no issues" in result.stdout
