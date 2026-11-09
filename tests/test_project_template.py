import os
import subprocess
import sys
from pathlib import Path

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
        assert (destination / ".gitignore").is_file()
        assert (destination / "Pipfile").is_file()
        assert (destination / "static_src" / "project.css").is_file()
        assert (destination / "templates" / "orion" / "base.html").is_file()

    def test_pipfile_includes_tailwind_cli(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        pipfile_content = (destination / "Pipfile").read_text()
        assert "django-tailwind-cli" in pipfile_content

    def test_project_css_imports_orions_static_src(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        css_content = (destination / "static_src" / "project.css").read_text()
        assert "__ORION_STATIC_SRC__" not in css_content
        assert "orion.css" in css_content

    @pytest.mark.parametrize(
        ("path", "is_ignored"),
        [
            (".env", True),
            ("static/orion/css/orion.css", True),
            ("media/original_images/a.jpg", True),
            ("private/forms/1/abc/cv.pdf", True),
            ("home/static/home/css/site.css", False),
            ("assets/project/css/project.css", False),
            ("AGENTS.md", False),
            ("CLAUDE.md", False),
        ],
    )
    def test_gitignore(self, tmp_path, monkeypatch, path, is_ignored):
        destination = tmp_path / "mysite"
        destination.mkdir()
        _run_orion_start(monkeypatch, "mysite", str(destination))
        subprocess.run(["git", "init", "-q"], cwd=destination, check=True)  # noqa: S607

        result = subprocess.run(  # noqa: S603
            ["git", "check-ignore", "-q", path],  # noqa: S607
            cwd=destination,
            check=False,
        )

        assert (result.returncode == 0) is is_ignored

    def test_project_stylesheet_exists_before_compiling(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()
        _run_orion_start(monkeypatch, "mysite", str(destination))

        env = {**os.environ, "DEBUG": "true", "DATABASE_URL": "postgres:///orion"}
        env.pop("DJANGO_SETTINGS_MODULE", None)
        result = subprocess.run(
            [sys.executable, "manage.py", "findstatic", "project/css/project.css"],
            cwd=destination,
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        assert "Found" in result.stdout

    @pytest.mark.parametrize(
        "command",
        [
            ["manage.py", "check"],
            ["-c", "import mysite.wsgi"],
        ],
    )
    def test_env_file_is_loaded_without_pipenv(self, tmp_path, monkeypatch, command):
        destination = tmp_path / "mysite"
        destination.mkdir()
        _run_orion_start(monkeypatch, "mysite", str(destination))
        (destination / ".env").write_text(
            "DEBUG=false\nSECRET_KEY=a#b$c(d)=e\nDATABASE_URL=postgres:///mysite\n"
        )
        environment = {
            name: value
            for name, value in os.environ.items()
            if name
            not in ("DEBUG", "SECRET_KEY", "DATABASE_URL", "DJANGO_SETTINGS_MODULE")
        }

        result = subprocess.run(  # noqa: S603
            [sys.executable, *command],
            cwd=destination,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, result.stderr

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

    def test_pipfile_points_to_orions_repository(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        pipfile_content = (destination / "Pipfile").read_text()
        assert "<organization>" not in pipfile_content
        assert "https://github.com/fscoscia/orion-cms.git" in pipfile_content

    def test_agents_file_links_the_guides(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        content = (destination / "AGENTS.md").read_text()
        for guide in ("empezar", "estilos-y-diseno", "trabajar-con-ia"):
            assert (
                f"https://github.com/fscoscia/orion-cms/blob/main/docs/guias/{guide}.md"
                in content
            )

    def test_delivers_instructions_for_ai_assistants(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        for filename in ("AGENTS.md", "CLAUDE.md"):
            content = (destination / filename).read_text()
            assert "# mysite" in content
            assert "__PROJECT_NAME__" not in content
        assert "AGENTS.md" in (destination / "CLAUDE.md").read_text()

    def test_agents_file_states_the_working_rules(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()

        _run_orion_start(monkeypatch, "mysite", str(destination))

        content = (destination / "AGENTS.md").read_text()
        # The project installs no pytest, so its test command is Django's.
        assert "pipenv run manage test" in content
        assert "pytest" not in content
        assert "mysite/settings.py" in content
        for heading in (
            "## Bloques de Orion o bloques propios",
            "## Contenido existente: cuidado",
            "## Actualizar Orion",
            "## Al terminar una tarea",
        ):
            assert heading in content
        # Template tags documented in the file are kept as written.
        assert "{% trans %}" in content

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

    def test_project_compiles_its_own_tailwind_css(self, tmp_path, monkeypatch):
        destination = tmp_path / "mysite"
        destination.mkdir()
        _run_orion_start(monkeypatch, "mysite", str(destination))

        orion_css = (
            Path(__file__).resolve().parent.parent
            / "src"
            / "orion"
            / "core"
            / "static"
            / "orion"
            / "css"
            / "orion.css"
        )
        orion_css_before = orion_css.read_text()

        env = {**os.environ, "DEBUG": "true", "DATABASE_URL": "postgres:///orion"}
        env.pop("DJANGO_SETTINGS_MODULE", None)
        result = subprocess.run(
            [sys.executable, "manage.py", "tailwind", "build"],
            cwd=destination,
            env=env,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, result.stderr
        dist_css = destination / "assets" / "project" / "css" / "project.css"
        assert dist_css.is_file()
        assert dist_css.stat().st_size > 0
        assert orion_css.read_text() == orion_css_before
