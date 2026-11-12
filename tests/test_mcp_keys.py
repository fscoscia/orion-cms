import datetime
import importlib

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import migrations
from django.test import RequestFactory
from django.utils import timezone

from orion.editor.roles import EDITORS_GROUP
from orion.mcp import auth
from orion.mcp.models import TOKEN_PREFIX, ApiKey, OperationReceipt, hash_token

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(django_user_model):
    account = django_user_model.objects.create_user("cliente", password="x")
    account.groups.add(Group.objects.get(name=EDITORS_GROUP))
    return account


def _request(token=None, header=None):
    extra = {}
    if header is not None:
        extra["HTTP_AUTHORIZATION"] = header
    elif token is not None:
        extra["HTTP_AUTHORIZATION"] = f"Bearer {token}"
    return RequestFactory().post("/_mcp/", **extra)


def test_a_key_has_a_token_with_the_prefix_and_only_its_hash_is_stored(user):
    key, token = ApiKey.issue(name="Claude", scope="read-only", user=user)

    assert token.startswith(TOKEN_PREFIX)
    assert len(token) == len(TOKEN_PREFIX) + 48
    assert key.key_hash == hash_token(token)
    assert key.prefix == token[: len(TOKEN_PREFIX) + 8]
    stored = [str(value) for value in ApiKey.objects.values().get().values()]
    assert not [value for value in stored if token in value]


def test_two_keys_have_different_tokens(user):
    _, first = ApiKey.issue(name="Uno", scope="read-only", user=user)
    _, second = ApiKey.issue(name="Dos", scope="read-only", user=user)

    assert first != second


def test_a_key_cannot_act_as_a_superuser(django_user_model):
    root = django_user_model.objects.create_superuser("root", password="x")

    with pytest.raises(ValidationError):
        ApiKey.issue(name="X", scope="read-only", user=root)
    assert not ApiKey.objects.exists()


def test_a_key_cannot_act_as_an_inactive_user(django_user_model):
    gone = django_user_model.objects.create_user("gone", password="x", is_active=False)

    with pytest.raises(ValidationError):
        ApiKey.issue(name="X", scope="read-only", user=gone)


def test_a_valid_key_authenticates(user):
    key, token = ApiKey.issue(name="Claude", scope="draft-only", user=user)

    assert auth.authenticate(_request(token)) == key


def _refused_cases(user):
    revoked, revoked_token = ApiKey.issue(name="R", scope="read-only", user=user)
    revoked.revoke()
    _, expired_token = ApiKey.issue(
        name="E",
        scope="read-only",
        user=user,
        expires_at=timezone.now() - datetime.timedelta(minutes=1),
    )
    return {
        "missing": _request(),
        "unknown": _request("orion_mcp_" + "x" * 48),
        "revoked": _request(revoked_token),
        "expired": _request(expired_token),
        "not bearer": _request(header="Basic abc"),
        "empty": _request(header="Bearer "),
    }


def test_a_key_that_cannot_be_used_is_refused(user):
    for label, request in _refused_cases(user).items():
        assert auth.authenticate(request) is None, label


def test_a_key_of_a_deactivated_user_stops_serving(user):
    _, token = ApiKey.issue(name="C", scope="read-only", user=user)
    assert auth.authenticate(_request(token)) is not None

    user.is_active = False
    user.save()

    assert auth.authenticate(_request(token)) is None


def test_a_key_of_a_user_who_became_a_superuser_stops_serving(user):
    _, token = ApiKey.issue(name="C", scope="read-only", user=user)

    user.is_superuser = True
    user.save()

    assert auth.authenticate(_request(token)) is None


def test_deleting_the_user_deletes_the_key(user):
    ApiKey.issue(name="C", scope="read-only", user=user)

    user.delete()

    assert not ApiKey.objects.exists()


def test_the_last_use_is_written_once_a_minute(user, django_assert_num_queries):
    key, _ = ApiKey.issue(name="C", scope="read-only", user=user)

    auth.record_use(key)
    first = ApiKey.objects.get(pk=key.pk).last_used_at
    with django_assert_num_queries(0):
        for _call in range(10):
            auth.record_use(key)

    assert first is not None
    assert ApiKey.objects.get(pk=key.pk).last_used_at == first


def test_status_follows_revocation_and_expiry(user):
    key, _ = ApiKey.issue(name="C", scope="read-only", user=user)
    assert key.status == "active"

    key.expires_at = timezone.now() - datetime.timedelta(seconds=1)
    assert key.status == "expired"

    key.revoke()
    assert key.status == "revoked"


def test_a_receipt_is_unique_per_key_tool_and_operation(user):
    key, _ = ApiKey.issue(name="C", scope="draft-only", user=user)
    OperationReceipt.objects.create(
        key=key,
        tool="page_create_draft",
        operation_key="a",
        payload_hash="h",
        result={},
    )

    with pytest.raises(
        Exception, match="orion_mcp_one_receipt_per_operation|Duplicate"
    ):
        OperationReceipt.objects.create(
            key=key,
            tool="page_create_draft",
            operation_key="a",
            payload_hash="h2",
            result={},
        )


def test_the_migration_only_creates_tables():
    module = importlib.import_module("orion.mcp.migrations.0001_api_keys_and_receipts")

    operations = module.Migration.operations
    assert operations
    assert all(isinstance(op, migrations.CreateModel) for op in operations)
    assert {op.name for op in operations} == {"ApiKey", "OperationReceipt"}
