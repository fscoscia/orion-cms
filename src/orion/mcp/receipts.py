"""Safe retries: a write made with an operation key is done once.

A client that does not know whether its write arrived repeats it with the same operation
key. The first time the result is stored in a receipt; the same key with the same
arguments then gives the stored result instead of writing again.
"""

import datetime
import hashlib
import json
import uuid

from django.core.cache import cache
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone

from orion.mcp.models import ApiKey, OperationReceipt
from orion.mcp.registry import ToolError

RECEIPT_LIFETIME = datetime.timedelta(days=30)
PURGE_INTERVAL = 3600  # seconds between purges


def _plain(data):
    """The data as JSON would keep it."""
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))


def payload_hash(arguments):
    canonical = json.dumps(
        arguments, sort_keys=True, separators=(",", ":"), cls=DjangoJSONEncoder
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


# Writes that take effect when saved and keep what they replaced, so they can be undone.
TRACKED_TOOLS = frozenset(
    {"redirect_create", "redirect_update", "site_settings_update", "site_texts_update"}
)


def new_operation_key():
    return f"auto-{uuid.uuid4().hex}"


def run_once(key, tool, operation_key, arguments, work, undo=None):
    """Run `work()` unless the key already did this operation; return its result.

    `undo()`, if given, is called after the work and gives what to keep for undoing it.
    """
    digest = payload_hash(arguments)
    with transaction.atomic():
        # Serialize the writes of one key, so two equal retries cannot both run.
        ApiKey.objects.select_for_update().get(pk=key.pk)
        receipt = OperationReceipt.objects.filter(
            key=key, tool=tool, operation_key=operation_key
        ).first()
        if receipt is not None:
            if receipt.payload_hash != digest:
                raise ToolError(
                    "This operation key was already used with other arguments. "
                    "Repeat the original call or choose a new operation key."
                )
            return receipt.result
        result = _plain(work())
        record = undo() if undo else None
        OperationReceipt.objects.create(
            key=key,
            tool=tool,
            operation_key=operation_key,
            payload_hash=digest,
            result=result,
            before=_plain(record) if record else None,
        )
    purge_old_receipts()
    return result


def purge_old_receipts():
    """Delete receipts older than their lifetime, at most once an hour."""
    if cache.add("orion_mcp_receipts_purged", 1, PURGE_INTERVAL):
        OperationReceipt.objects.filter(
            created_at__lt=timezone.now() - RECEIPT_LIFETIME
        ).delete()
