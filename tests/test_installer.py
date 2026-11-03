import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import OperationalError, connections

from orion.forms.models import FormPage

pytestmark = pytest.mark.django_db

SUPERUSER_ENV = {
    "DJANGO_SUPERUSER_USERNAME": "admin",
    "DJANGO_SUPERUSER_EMAIL": "admin@example.com",
    "DJANGO_SUPERUSER_PASSWORD": "a-strong-password-123",
}


@pytest.fixture(autouse=True)
def installer_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.ORION_FORMS_PRIVATE_ROOT = str(tmp_path / "private")
    return settings


@pytest.fixture(autouse=True)
def superuser_env(monkeypatch):
    for key, value in SUPERUSER_ENV.items():
        monkeypatch.setenv(key, value)


class TestInstaller:
    def test_fresh_installation(self):
        call_command("orion_install", "--noinput")

        assert (
            get_user_model()
            .objects.filter(username="admin", is_superuser=True)
            .exists()
        )
        assert FormPage.objects.filter(title="Contacto").exists()
        assert FormPage.objects.filter(title="Trabajá con nosotros").exists()

    def test_noinput_does_not_prompt(self, monkeypatch):
        def _must_not_prompt(*args, **kwargs):
            raise AssertionError("must not prompt with --noinput")

        monkeypatch.setattr("builtins.input", _must_not_prompt)

        call_command("orion_install", "--noinput")

        assert get_user_model().objects.filter(username="admin").exists()

    def test_running_twice_does_not_duplicate_or_fail(self):
        call_command("orion_install", "--noinput")
        call_command("orion_install", "--noinput")

        assert get_user_model().objects.filter(username="admin").count() == 1
        assert FormPage.objects.filter(title="Contacto").count() == 1
        assert FormPage.objects.filter(title="Trabajá con nosotros").count() == 1

    def test_fails_before_migrating_when_database_is_unreachable(self, monkeypatch):
        def _unreachable():
            raise OperationalError("could not connect")

        monkeypatch.setattr(connections["default"], "ensure_connection", _unreachable)

        def _must_not_run(name, *args, **kwargs):
            raise AssertionError(f"must not call {name} when the database is down")

        monkeypatch.setattr(
            "orion.core.management.commands.orion_install.call_command", _must_not_run
        )

        with pytest.raises(CommandError):
            call_command("orion_install", "--noinput")
