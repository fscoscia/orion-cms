import pytest
from django.conf.urls.i18n import is_language_prefix_patterns_used
from wagtail.coreutils import get_supported_content_language_variant

from orion.core.checks import EMAIL_SSL_AND_TLS_ERROR_ID, check_email_security
from orion.localization.checks import (
    BASE_LANGUAGE_NOT_IN_CATALOG_ERROR_ID,
    MISSING_LANGUAGE_URLS_ERROR_ID,
    check_base_language_in_catalog,
    check_language_urls,
)


def test_ssl_and_tls_together_is_an_error(settings):
    settings.EMAIL_USE_SSL = True
    settings.EMAIL_USE_TLS = True

    errors = check_email_security(app_configs=None)

    assert [error.id for error in errors] == [EMAIL_SSL_AND_TLS_ERROR_ID]


def test_only_one_of_ssl_or_tls_passes(settings):
    settings.EMAIL_USE_SSL = False
    settings.EMAIL_USE_TLS = True
    assert check_email_security(app_configs=None) == []

    settings.EMAIL_USE_SSL = True
    settings.EMAIL_USE_TLS = False
    assert check_email_security(app_configs=None) == []


class TestBaseLanguageCheck:
    @pytest.fixture(autouse=True)
    def _clear_language_caches(self):
        get_supported_content_language_variant.cache_clear()
        yield
        get_supported_content_language_variant.cache_clear()

    def test_base_language_in_catalog_passes(self, settings):
        settings.LANGUAGE_CODE = "es"

        assert check_base_language_in_catalog(app_configs=None) == []

    def test_base_language_outside_catalog_is_an_error(self, settings):
        settings.LANGUAGE_CODE = "xx"

        errors = check_base_language_in_catalog(app_configs=None)

        assert [error.id for error in errors] == [BASE_LANGUAGE_NOT_IN_CATALOG_ERROR_ID]
        assert "xx" in errors[0].msg


class TestLanguageUrlsCheck:
    @pytest.fixture(autouse=True)
    def _clear_url_caches(self):
        is_language_prefix_patterns_used.cache_clear()
        yield
        is_language_prefix_patterns_used.cache_clear()

    def test_project_urls_with_language_routes_pass(self):
        assert check_language_urls(app_configs=None) == []

    def test_urlconf_without_language_routes_is_an_error(self, settings):
        settings.ROOT_URLCONF = "tests.urls_without_languages"

        errors = check_language_urls(app_configs=None)

        assert [error.id for error in errors] == [MISSING_LANGUAGE_URLS_ERROR_ID]
