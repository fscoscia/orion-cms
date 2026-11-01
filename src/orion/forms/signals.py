import logging

from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from orion.forms.models import FormSubmission
from orion.forms.storage import get_private_storage

logger = logging.getLogger(__name__)


def delete_attachments(submission):
    """Delete the submission's files; return how many existed."""
    storage = get_private_storage()
    deleted = 0
    for _name, value in submission.attachments():
        if storage.exists(value["path"]):
            storage.delete(value["path"])
            deleted += 1
    return deleted


@receiver(post_delete, sender=FormSubmission, dispatch_uid="orion_forms_attachments")
def delete_attachments_with_the_submission(sender, instance, **kwargs):
    # After the commit: a rolled back deletion must keep its files.
    transaction.on_commit(lambda: delete_attachments(instance))
