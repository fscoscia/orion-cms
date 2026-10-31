import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import Group
from django.core import mail
from django.urls import reverse
from wagtail.models import Page

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP

pytestmark = pytest.mark.django_db


@pytest.fixture
def make_user(django_user_model):
    def _make(username, group_name):
        user = django_user_model.objects.create_user(
            username, email=f"{username}@example.com", password="x"
        )
        user.groups.add(Group.objects.get(name=group_name))
        return user

    return _make


def _edit_form_data(client, page):
    """The fields of the page's edit form, as the browser would send them."""
    html = client.get(reverse("wagtailadmin_pages:edit", args=[page.pk])).content
    form = BeautifulSoup(html, "html.parser").select_one("form[data-edit-form]")
    data = {}
    for field in form.select("input[name], textarea[name], select[name]"):
        if field.get("type") in ("checkbox", "radio") and not field.has_attr("checked"):
            continue
        if field.name == "textarea":
            value = field.text
        elif field.name == "select":
            option = field.select_one("option[selected]")
            value = option["value"] if option else ""
        else:
            value = field.get("value", "")
        data[field["name"]] = value
    return form, data


class TestAutosave:
    def test_editor_form_autosaves(self, admin_client, services_page):
        form, _data = _edit_form_data(admin_client, services_page)

        assert "w-autosave" in form["data-controller"].split()

    def test_autosave_keeps_a_draft_and_does_not_publish(
        self, client, make_user, services_page
    ):
        client.force_login(make_user("ana", EDITORS_GROUP))
        _form, data = _edit_form_data(client, services_page)
        data["title"] = "Servicios (borrador)"

        response = client.post(
            reverse("wagtailadmin_pages:edit", args=[services_page.pk]),
            data,
            HTTP_ACCEPT="application/json",
        )

        page = Page.objects.get(pk=services_page.pk)
        assert response.json()["success"] is True
        assert page.title == "Servicios"
        assert page.has_unpublished_changes
        assert page.get_latest_revision_as_object().title == "Servicios (borrador)"


class TestApprovalEmails:
    def test_submitting_notifies_administrators_and_rejecting_the_author(
        self, settings, make_user, services_page, django_capture_on_commit_callbacks
    ):
        settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
        settings.WAGTAILADMIN_BASE_URL = "https://cms.example.com"
        editor = make_user("ana", EDITORS_GROUP)
        administrator = make_user("jefa", ADMINISTRATORS_GROUP)
        services_page.title = "Servicios (revisado)"
        services_page.save_revision(user=editor)

        with django_capture_on_commit_callbacks(execute=True):
            workflow_state = services_page.get_workflow().start(services_page, editor)
        submitted = list(mail.outbox)
        mail.outbox.clear()
        task_state = workflow_state.current_task_state
        with django_capture_on_commit_callbacks(execute=True):
            task_state.task.specific.on_action(
                task_state, administrator, "reject", comment="Falta la foto"
            )

        assert [message.to for message in submitted] == [[administrator.email]]
        assert "https://cms.example.com/admin/" in submitted[0].body
        assert [message.to for message in mail.outbox] == [[editor.email]]
