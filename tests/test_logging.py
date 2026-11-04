import io
import logging

import pytest
from django.http import HttpResponse
from django.urls import path

pytestmark = pytest.mark.django_db


def broken_view(request):
    raise RuntimeError("orion-test-failure")


def working_view(request):
    return HttpResponse("ok")


urlpatterns = [path("broken/", broken_view), path("working/", working_view)]


@pytest.fixture
def error_output():
    """What reaches the console handler of the base settings."""
    handler = next(h for h in logging.getLogger().handlers if h.name == "console")
    output = io.StringIO()
    previous_stream = handler.setStream(output)
    yield output
    handler.setStream(previous_stream)


@pytest.fixture
def client_with_errors(client, settings):
    settings.ROOT_URLCONF = __name__
    client.raise_request_exception = False
    return client


def test_unhandled_error_is_logged_with_its_traceback(client_with_errors, error_output):
    response = client_with_errors.get("/broken/")

    assert response.status_code == 500
    assert "Traceback" in error_output.getvalue()
    assert "orion-test-failure" in error_output.getvalue()


def test_error_logged_by_orion_reaches_the_output(error_output):
    logging.getLogger("orion.forms.models").error("orion-test-notice")

    assert "orion-test-notice" in error_output.getvalue()


def test_not_found_is_not_logged(client_with_errors, error_output):
    response = client_with_errors.get("/missing/")

    assert response.status_code == 404
    assert error_output.getvalue() == ""


def test_disallowed_host_is_not_logged(client_with_errors, error_output):
    response = client_with_errors.get("/working/", headers={"host": "evil.test"})

    assert response.status_code == 400
    assert error_output.getvalue() == ""
