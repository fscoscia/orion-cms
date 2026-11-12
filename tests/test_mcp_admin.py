import json

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.mcp.models import ApiKey

pytestmark = pytest.mark.django_db

LIST = "orion_mcp_keys"
NEW = "orion_mcp_key_new"


@pytest.fixture
def make_user(django_user_model):
    def _make(name, group):
        account = django_user_model.objects.create_user(
            name, email=f"{name}@example.com", password="x"
        )
        account.groups.add(Group.objects.get(name=group))
        return account

    return _make


@pytest.fixture
def administrator(make_user, client):
    account = make_user("jefa", ADMINISTRATORS_GROUP)
    client.force_login(account)
    return account


@pytest.fixture
def editor_client(make_user):
    client = Client()
    client.force_login(make_user("editora", EDITORS_GROUP))
    return client


@pytest.fixture
def key_user(make_user):
    return make_user("cliente", EDITORS_GROUP)


def _create(client, key_user, **extra):
    data = {"name": "Claude", "user": key_user.pk, "scope": "draft-only", **extra}
    return client.post(reverse(NEW), data)


def test_an_administrator_sees_the_list(administrator, client, key_user):
    ApiKey.issue(name="Existente", scope="read-only", user=key_user)

    response = client.get(reverse(LIST))
    html = response.content.decode()

    assert response.status_code == 200
    assert "Existente" in html
    assert "cliente" in html


def test_the_list_warns_when_the_endpoint_is_off(administrator, client, settings):
    settings.ORION_MCP_ENDPOINT = False

    assert "ORION_MCP_ENDPOINT" in client.get(reverse(LIST)).content.decode()


def test_creating_a_key_shows_the_token_once(administrator, client, key_user):
    response = _create(client, key_user)

    key = ApiKey.objects.get()
    token = next(
        word
        for word in response.content.decode()
        .replace("<", " ")
        .replace(">", " ")
        .split()
        if word.startswith("orion_mcp_") and len(word) > 30
    )
    assert response.status_code == 200
    assert "no-store" in response["Cache-Control"]
    assert key.key_hash != token
    assert key.created_by == administrator
    assert key.user == key_user
    listing = client.get(reverse(LIST)).content.decode()
    assert token not in listing
    assert key.prefix in listing


@pytest.mark.mcp_endpoint
def test_a_created_key_works_against_the_endpoint(
    administrator, client, key_user, settings
):
    settings.ORION_MCP_ENDPOINT = True
    response = _create(client, key_user)
    token = next(
        word
        for word in response.content.decode()
        .replace("<", " ")
        .replace(">", " ")
        .split()
        if word.startswith("orion_mcp_") and len(word) > 30
    )

    answer = Client().post(
        "/_mcp/",
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",
    )

    assert answer.status_code == 200


def test_a_superuser_cannot_be_chosen(administrator, client, django_user_model):
    root = django_user_model.objects.create_superuser("root", password="x")

    response = _create(client, root)

    assert not ApiKey.objects.exists()
    assert response.status_code == 200  # the form again, with the error


def test_an_inactive_user_cannot_be_chosen(administrator, client, django_user_model):
    gone = django_user_model.objects.create_user("gone", password="x", is_active=False)

    _create(client, gone)

    assert not ApiKey.objects.exists()


@pytest.mark.mcp_endpoint
def test_revoking_stops_the_key(administrator, client, key_user, settings):
    settings.ORION_MCP_ENDPOINT = True
    key, token = ApiKey.issue(name="C", scope="read-only", user=key_user)
    message = {"jsonrpc": "2.0", "id": 1, "method": "ping"}

    def call():
        return Client().post(
            "/_mcp/",
            data=json.dumps(message),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

    assert call().status_code == 200
    response = client.post(reverse("orion_mcp_key_revoke", args=[key.pk]))

    assert response.status_code == 302
    key.refresh_from_db()
    assert key.revoked_at is not None
    assert call().status_code == 401


def test_revoking_needs_a_post(administrator, client, key_user):
    key, _ = ApiKey.issue(name="C", scope="read-only", user=key_user)

    response = client.get(reverse("orion_mcp_key_revoke", args=[key.pk]))

    assert response.status_code == 405
    key.refresh_from_db()
    assert key.revoked_at is None


def test_an_editor_cannot_reach_the_screens(editor_client, key_user):
    key, _ = ApiKey.issue(name="C", scope="read-only", user=key_user)

    # Wagtail answers a refused admin page by sending the user back to the home.
    responses = [
        editor_client.get(reverse(LIST)),
        editor_client.get(reverse(NEW)),
        _create(editor_client, key_user),
        editor_client.post(reverse("orion_mcp_key_revoke", args=[key.pk])),
    ]

    for response in responses:
        assert response.status_code in (302, 403)
        assert response.status_code != 200
    key.refresh_from_db()
    assert key.revoked_at is None
    assert ApiKey.objects.count() == 1


def test_the_menu_shows_the_screen_to_administrators_only(
    administrator, client, editor_client
):
    home = reverse("wagtailadmin_home")

    assert reverse(LIST) in client.get(home).content.decode()
    assert reverse(LIST) not in editor_client.get(home).content.decode()


def test_the_screens_are_translated(administrator, client, key_user):
    ApiKey.issue(name="C", scope="read-only", user=key_user)

    html = client.get(reverse(LIST), HTTP_ACCEPT_LANGUAGE="es").content.decode()

    assert "Claves de API" in html
    assert "Crear una clave" in html
    assert "Create a key" not in html


def test_only_a_superuser_can_create_a_full_key(
    client, administrator, key_user, django_user_model
):
    client.force_login(administrator)
    editor = key_user
    form = client.get(reverse("orion_mcp_key_new")).content.decode()
    assert 'value="full"' not in form

    client.post(
        reverse("orion_mcp_key_new"), {"name": "F", "user": editor.pk, "scope": "full"}
    )
    assert not ApiKey.objects.filter(name="F").exists()

    root = django_user_model.objects.create_superuser("root", password="x")
    client.force_login(root)
    assert 'value="full"' in client.get(reverse("orion_mcp_key_new")).content.decode()
    client.post(
        reverse("orion_mcp_key_new"), {"name": "F", "user": editor.pk, "scope": "full"}
    )
    assert ApiKey.objects.get(name="F").scope == "full"


def test_an_administrator_can_revoke_a_full_key(client, administrator):
    client.force_login(administrator)
    key, _ = ApiKey.issue(name="Completa", scope="full", user=administrator)

    client.post(reverse("orion_mcp_key_revoke", args=[key.pk]))

    key.refresh_from_db()
    assert key.revoked_at is not None
