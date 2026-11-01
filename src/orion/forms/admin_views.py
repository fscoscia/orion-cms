"""Admin views of orion.forms: download an attachment and send a test email."""

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET, require_http_methods
from wagtail.contrib.forms.utils import get_forms_for_user

from orion.forms.models import (
    FormPage,
    FormSubmission,
    SubmissionNote,
    SubmissionStatus,
)
from orion.forms.storage import get_private_storage


def _get_submission(request, submission_id):
    """The submission, if the user may see the submissions of its form."""
    submission = get_object_or_404(FormSubmission, pk=submission_id)
    if not get_forms_for_user(request.user).filter(pk=submission.page_id).exists():
        raise PermissionDenied
    return submission


@require_GET
def attachment(request, submission_id, field_name):
    submission = _get_submission(request, submission_id)
    value = submission.form_data.get(field_name)
    if not isinstance(value, dict) or "path" not in value:
        raise Http404
    storage = get_private_storage()
    if not storage.exists(value["path"]):
        raise Http404
    response = FileResponse(
        storage.open(value["path"], "rb"), as_attachment=True, filename=value["name"]
    )
    response["X-Content-Type-Options"] = "nosniff"
    return response


@require_http_methods(["GET", "POST"])
def test_email(request, page_id):
    page = get_object_or_404(FormPage, pk=page_id)
    if not page.permissions_for_user(request.user).can_edit():
        raise PermissionDenied
    recipients = page.get_recipients()
    if request.method == "POST":
        if not recipients:
            messages.error(request, _("Add at least one recipient first."))
        else:
            message = EmailMessage(
                subject=gettext("[Test] %(subject)s")
                % {"subject": page.subject or page.title},
                body=gettext(
                    "This is a test of the email notice of the form "
                    '"%(form)s". Submissions will arrive like this.'
                )
                % {"form": page.title},
                from_email=page.get_from_email(),
                to=recipients,
            )
            try:
                message.send()
            except Exception as error:  # noqa: BLE001 - shown to the editor
                messages.error(
                    request,
                    _("The test email could not be sent: %(error)s") % {"error": error},
                )
            else:
                messages.success(
                    request,
                    _("Test email sent to %(recipients)s.")
                    % {"recipients": ", ".join(recipients)},
                )
        return redirect("wagtailadmin_pages:edit", page.pk)
    return TemplateResponse(
        request,
        "orion/forms/admin/test_email.html",
        {"page": page, "recipients": recipients},
    )


@require_http_methods(["GET", "POST"])
def submission_detail(request, submission_id):
    """A submission's data and attachments, with its status and internal notes."""
    submission = _get_submission(request, submission_id)
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "status" and request.POST.get("status") in SubmissionStatus:
            submission.status = request.POST["status"]
            submission.save(update_fields=["status"])
            messages.success(request, _("Status updated."))
        elif action == "note":
            text = request.POST.get("text", "").strip()[:2000]
            if text:
                SubmissionNote.objects.create(
                    submission=submission, author=request.user, text=text
                )
                messages.success(request, _("Note added."))
            else:
                messages.error(request, _("Write the note first."))
        return redirect("orion_form_submission", submission.pk)
    if submission.status == SubmissionStatus.NEW:
        submission.status = SubmissionStatus.READ
        submission.save(update_fields=["status"])
    page = submission.page.specific
    labels = {field.clean_name: field.label for field in page.get_form_fields()}
    attachments = dict(submission.attachments())
    values = []
    for name, value in submission.form_data.items():
        if name in attachments:
            continue
        if isinstance(value, list):
            value = ", ".join(map(str, value))
        values.append((labels.get(name, name), "" if value is None else value))
    return TemplateResponse(
        request,
        "orion/forms/admin/submission_detail.html",
        {
            "submission": submission,
            "page": page,
            "values": values,
            "attachments": [
                (labels.get(name, name), name, value["name"])
                for name, value in attachments.items()
            ],
            "statuses": SubmissionStatus.choices,
            "notes": submission.notes.select_related("author"),
        },
    )
