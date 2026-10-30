from unittest import mock

import pytest
from django.db import OperationalError
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_reports_ok_when_database_responds(client):
    response = client.get(reverse("health_check"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_reports_error_without_details_when_database_fails(client):
    database_error = OperationalError("could not connect to server: secret-host")

    with mock.patch("orion.core.views.connection.cursor", side_effect=database_error):
        response = client.get(reverse("health_check"))

    assert response.status_code == 503
    assert response.json() == {"status": "error"}
    assert b"secret-host" not in response.content


def test_response_is_not_cached(client):
    response = client.get(reverse("health_check"))

    assert "no-store" in response["Cache-Control"]


def test_head_is_allowed(client):
    assert client.head(reverse("health_check")).status_code == 200


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_write_methods_are_rejected(client, method):
    response = getattr(client, method)(reverse("health_check"))

    assert response.status_code == 405
