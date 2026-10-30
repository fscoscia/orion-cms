from orion.core.checks import EMAIL_SSL_AND_TLS_ERROR_ID, check_email_security


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
