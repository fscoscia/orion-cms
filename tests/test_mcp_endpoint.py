import json
import logging

import pytest
from django.contrib.auth.models import Group
from django.test import Client, RequestFactory

from orion.core.paths import is_internal_request
from orion.editor.roles import EDITORS_GROUP
from orion.mcp import limits
from orion.mcp.models import ApiKey
from orion.seo.models import NotFoundPath

pytestmark = [pytest.mark.django_db, pytest.mark.mcp_endpoint]

URL = "/_mcp/"


@pytest.fixture
def endpoint(settings):
    settings.ORION_MCP_ENDPOINT = True
    return settings


@pytest.fixture
def user(django_user_model):
    account = django_user_model.objects.create_user("cliente", password="x")
    account.groups.add(Group.objects.get(name=EDITORS_GROUP))
    return account


@pytest.fixture
def token(user):
    return ApiKey.issue(name="Claude", scope="draft-only", user=user)[1]


def _post(token, message, client=None, **extra):
    client = client or Client()
    if token is not None:
        extra["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return client.post(
        URL, data=json.dumps(message), content_type="application/json", **extra
    )


INITIALIZE = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
LIST = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}


# On and off


def test_the_endpoint_is_off_by_default(token):
    response = _post(token, INITIALIZE)

    assert response.status_code == 404


def test_an_off_endpoint_is_not_recorded_as_a_missing_page(token):
    Client().get(URL)

    assert not NotFoundPath.objects.exists()


def test_an_initialize_with_a_valid_key_answers_json(endpoint, token):
    response = _post(token, INITIALIZE)

    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert response.json()["result"]["serverInfo"]["name"] == "orion"
    assert response["Cache-Control"] == "no-store"


def test_a_notification_gets_202_without_a_body(endpoint, token):
    response = _post(token, {"jsonrpc": "2.0", "method": "notifications/initialized"})

    assert response.status_code == 202
    assert response.content == b""


@pytest.mark.parametrize("method", ["get", "delete", "put"])
def test_other_methods_get_405(endpoint, token, method):
    response = getattr(Client(), method)(URL, HTTP_AUTHORIZATION=f"Bearer {token}")

    assert response.status_code == 405
    assert response["Allow"] == "POST"
    assert response["Cache-Control"] == "no-store"


def test_no_session_or_csrf_is_needed(endpoint, token):
    client = Client(enforce_csrf_checks=True)

    response = _post(token, INITIALIZE, client=client)

    assert response.status_code == 200


def test_invalid_json_is_a_parse_error(endpoint, token):
    response = Client().post(
        URL,
        data="{nope",
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == -32700


# Headers and size


def test_a_browser_origin_is_refused(endpoint, token):
    response = _post(token, INITIALIZE, HTTP_ORIGIN="https://otro.example")

    assert response.status_code == 403


def test_a_listed_origin_is_accepted(endpoint, token):
    endpoint.ORION_MCP_ALLOWED_ORIGINS = ["https://claude.example"]

    response = _post(token, INITIALIZE, HTTP_ORIGIN="https://claude.example")

    assert response.status_code == 200


def test_an_unknown_protocol_version_header_is_refused(endpoint, token):
    response = _post(token, INITIALIZE, HTTP_MCP_PROTOCOL_VERSION="1999-01-01")

    assert response.status_code == 400


def test_a_known_protocol_version_header_is_accepted(endpoint, token):
    response = _post(token, INITIALIZE, HTTP_MCP_PROTOCOL_VERSION="2025-06-18")

    assert response.status_code == 200


def test_a_body_over_the_limit_is_refused_even_without_a_key(endpoint):
    endpoint.ORION_MCP_MAX_BODY = 100
    big = {"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {"x": "y" * 500}}

    response = _post(None, big)

    assert response.status_code == 413


# Authentication


def test_every_unusable_key_gets_the_same_answer(endpoint, user):
    revoked, revoked_token = ApiKey.issue(name="R", scope="read-only", user=user)
    revoked.revoke()

    answers = {
        "none": _post(None, INITIALIZE),
        "unknown": _post("orion_mcp_" + "x" * 48, INITIALIZE),
        "revoked": _post(revoked_token, INITIALIZE),
    }

    contents = {label: response.content for label, response in answers.items()}
    assert len(set(contents.values())) == 1, contents
    for response in answers.values():
        assert response.status_code == 401
        assert response["WWW-Authenticate"].startswith("Bearer")
        assert response["Cache-Control"] == "no-store"


def test_a_revoked_key_stops_on_the_next_request(endpoint, user):
    key, token = ApiKey.issue(name="C", scope="read-only", user=user)
    assert _post(token, INITIALIZE).status_code == 200

    key.revoke()

    assert _post(token, INITIALIZE).status_code == 401


# Limits


def test_too_many_failed_attempts_block_the_address(endpoint, token):
    for _attempt in range(limits.FAILED_AUTH_LIMIT):
        assert _post("orion_mcp_" + "x" * 48, INITIALIZE).status_code == 401

    blocked = _post(token, INITIALIZE)

    assert blocked.status_code == 429
    assert int(blocked["Retry-After"]) >= 1


def test_a_key_over_its_rate_gets_429_with_retry_after(endpoint, token):
    endpoint.ORION_MCP_RATE_LIMIT = 3

    codes = [
        _post(token, {"jsonrpc": "2.0", "id": n, "method": "ping"}).status_code
        for n in range(5)
    ]

    assert codes == [200, 200, 200, 429, 429]
    limited = _post(token, INITIALIZE)
    assert int(limited["Retry-After"]) >= 1


def test_the_limit_is_per_key(endpoint, user, token):
    endpoint.ORION_MCP_RATE_LIMIT = 1
    _, other = ApiKey.issue(name="Otra", scope="read-only", user=user)
    _post(token, INITIALIZE)

    assert _post(token, INITIALIZE).status_code == 429
    assert _post(other, INITIALIZE).status_code == 200


# Not a public page


def test_the_path_is_internal():
    assert is_internal_request(RequestFactory().get(URL))
    assert is_internal_request(RequestFactory().post(URL))


@pytest.mark.page_cache
def test_the_endpoint_is_not_cached_or_counted_as_a_missing_page(endpoint, token):
    first = Client().get(URL)
    second = Client().get(URL)

    assert first.status_code == second.status_code == 405
    assert second["Cache-Control"] == "no-store"
    assert not NotFoundPath.objects.exists()


# Logging


def test_each_call_is_logged_without_the_token_or_the_arguments(
    endpoint, token, caplog
):
    caplog.set_level(logging.INFO, logger="orion.mcp.views")
    message = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "page_get", "arguments": {"id": 999999}},
    }

    _post(token, message)

    text = " ".join(record.getMessage() for record in caplog.records)
    assert token[:18] in text
    assert "page_get" in text
    assert "result=error" in text
    assert token not in text
    assert "999999" not in text


def test_an_end_to_end_session(endpoint, token):
    assert _post(token, INITIALIZE).status_code == 200
    assert (
        _post(
            token, {"jsonrpc": "2.0", "method": "notifications/initialized"}
        ).status_code
        == 202
    )
    names = {tool["name"] for tool in _post(token, LIST).json()["result"]["tools"]}

    assert "page_get" in names
    assert "page_create_draft" in names  # a draft-only key
    assert "redirect_create" not in names


def test_the_call_log_reaches_the_error_output_handler(endpoint, token):
    import io

    handler = next(
        h for h in logging.getLogger("orion.mcp").handlers if h.name == "mcp"
    )
    output = io.StringIO()
    previous = handler.setStream(output)
    try:
        _post(token, {"jsonrpc": "2.0", "id": 1, "method": "ping"})
    finally:
        handler.setStream(previous)

    assert f"key={token[:18]}" in output.getvalue()
    assert token not in output.getvalue()
