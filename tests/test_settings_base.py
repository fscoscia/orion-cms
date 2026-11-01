import importlib
import re
from pathlib import Path

import pytest
from django.core.exceptions import ImproperlyConfigured

import orion.settings.base
from orion.settings.validators import validate_admin_path

POSTGRES_URL = "postgres://user:secret@db.example.com:5432/orion"
MYSQL_URL = "mysql://user:secret@db.example.com:3306/orion"

# Every variable the base settings read, taken from their source so the list cannot
# fall behind when a new one is added.
SETTINGS_VARIABLES = sorted(
    set(
        re.findall(
            r'env_\w+\(\s*"([A-Z0-9_]+)"',
            Path(orion.settings.base.__file__).read_text(),
        )
    )
)


@pytest.fixture
def load_settings(monkeypatch):
    """Reload the base settings module under a controlled environment.

    The module reads the environment at import time, so each scenario reloads it.
    The original module state is restored afterwards for the rest of the suite.
    """
    for name in SETTINGS_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DATABASE_URL", POSTGRES_URL)

    def _load(**environment):
        for name, value in environment.items():
            monkeypatch.setenv(name, value)
        return importlib.reload(orion.settings.base)

    yield _load
    monkeypatch.undo()
    importlib.reload(orion.settings.base)


ENV_EXAMPLE = Path(__file__).resolve().parent.parent / ".env.example"


def test_env_example_lists_every_settings_variable():
    listed = set(
        re.findall(r"^#?\s*([A-Z0-9_]+)=", ENV_EXAMPLE.read_text(), re.MULTILINE)
    )
    assert set(SETTINGS_VARIABLES) - listed == set()


class TestDebugAndSecretKey:
    def test_debug_is_off_by_default(self, load_settings):
        settings = load_settings(SECRET_KEY="production-secret")
        assert settings.DEBUG is False

    def test_secret_key_is_required_outside_debug(self, load_settings):
        with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
            load_settings()

    def test_debug_falls_back_to_development_key(self, load_settings):
        settings = load_settings(DEBUG="true")
        assert settings.SECRET_KEY.startswith("django-insecure-")

    def test_invalid_boolean_stops_startup(self, load_settings):
        with pytest.raises(ImproperlyConfigured, match="DEBUG"):
            load_settings(DEBUG="ture")


class TestHosts:
    def test_hosts_come_from_comma_separated_variable(self, load_settings):
        settings = load_settings(
            SECRET_KEY="production-secret",
            ALLOWED_HOSTS="example.com,www.example.com",
        )
        assert settings.ALLOWED_HOSTS == ["example.com", "www.example.com"]

    def test_no_hosts_allowed_by_default_in_production(self, load_settings):
        settings = load_settings(SECRET_KEY="production-secret")
        assert settings.ALLOWED_HOSTS == []


class TestDatabase:
    def test_database_url_is_required(self, load_settings, monkeypatch):
        monkeypatch.delenv("DATABASE_URL")
        with pytest.raises(ImproperlyConfigured, match="DATABASE_URL"):
            load_settings(DEBUG="true")

    def test_postgres_url(self, load_settings):
        settings = load_settings(DEBUG="true", DATABASE_URL=POSTGRES_URL)
        database = settings.DATABASES["default"]
        assert database["ENGINE"] == "django.db.backends.postgresql"
        assert database["NAME"] == "orion"
        assert database["HOST"] == "db.example.com"

    def test_mysql_url_enables_strict_mode(self, load_settings):
        settings = load_settings(DEBUG="true", DATABASE_URL=MYSQL_URL)
        database = settings.DATABASES["default"]
        assert database["ENGINE"] == "django.db.backends.mysql"
        assert "STRICT_TRANS_TABLES" in database["OPTIONS"]["init_command"]


class TestSecurityDefaults:
    def test_production_cookies_are_secure(self, load_settings):
        settings = load_settings(SECRET_KEY="production-secret")
        assert settings.SESSION_COOKIE_SECURE is True
        assert settings.CSRF_COOKIE_SECURE is True
        assert settings.SESSION_COOKIE_HTTPONLY is True
        assert settings.X_FRAME_OPTIONS == "SAMEORIGIN"

    def test_debug_allows_plain_http_cookies(self, load_settings):
        settings = load_settings(DEBUG="true")
        assert settings.SESSION_COOKIE_SECURE is False
        assert settings.CSRF_COOKIE_SECURE is False


class TestEmailBackend:
    def test_smtp_when_host_is_configured(self, load_settings):
        settings = load_settings(
            SECRET_KEY="production-secret", EMAIL_HOST="mail.example.com"
        )
        assert settings.EMAIL_BACKEND == "orion.integrations.mail.EmailBackend"

    def test_console_in_debug_without_host(self, load_settings):
        settings = load_settings(DEBUG="true")
        assert settings.EMAIL_BACKEND.endswith("console.EmailBackend")

    def test_discards_emails_in_production_without_host(self, load_settings):
        settings = load_settings(SECRET_KEY="production-secret")
        assert settings.EMAIL_BACKEND.endswith("dummy.EmailBackend")


class TestEmailEncryption:
    def test_tls_by_default(self, load_settings):
        settings = load_settings(DEBUG="true")
        assert settings.EMAIL_USE_TLS is True
        assert settings.EMAIL_USE_SSL is False

    def test_ssl_alone_turns_tls_off(self, load_settings):
        settings = load_settings(DEBUG="true", EMAIL_USE_SSL="true")
        assert settings.EMAIL_USE_SSL is True
        assert settings.EMAIL_USE_TLS is False

    def test_tls_can_be_disabled(self, load_settings):
        settings = load_settings(DEBUG="true", EMAIL_USE_TLS="false")
        assert settings.EMAIL_USE_TLS is False
        assert settings.EMAIL_USE_SSL is False


class TestAdminPath:
    def test_default_admin_path(self, load_settings):
        settings = load_settings(DEBUG="true")
        assert settings.ORION_ADMIN_PATH == "admin/"

    def test_custom_admin_path(self, load_settings):
        settings = load_settings(DEBUG="true", ORION_ADMIN_PATH="panel/")
        assert settings.ORION_ADMIN_PATH == "panel/"

    @pytest.mark.parametrize(
        "admin_path",
        ["", "/panel/", "panel", "pa nel/", "Panel/", "panel//", "../admin/"],
    )
    def test_invalid_admin_paths_are_rejected(self, admin_path):
        with pytest.raises(ImproperlyConfigured, match="ORION_ADMIN_PATH"):
            validate_admin_path(admin_path)

    def test_nested_admin_path_is_accepted(self):
        assert validate_admin_path("equipo/panel-2/") == "equipo/panel-2/"
