import importlib

import pytest
from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.urls import reverse
from wagtail.models import (
    GroupCollectionPermission,
    GroupPagePermission,
    Page,
    Workflow,
)

from orion.editor.roles import (
    ADMINISTRATORS_GROUP,
    EDITORS_GROUP,
    is_site_administrator,
)
from orion.pages.models import ArticleIndexPage, ContentPage

pytestmark = pytest.mark.django_db

roles_migration = importlib.import_module("orion.editor.migrations.0001_roles")


@pytest.fixture
def make_user(django_user_model):
    def _make(username, group_name=None):
        user = django_user_model.objects.create_user(username, password="x")
        if group_name:
            user.groups.add(Group.objects.get(name=group_name))
        return user

    return _make


@pytest.fixture
def content_page(home_page):
    page = ContentPage(title="Nosotros", slug="nosotros")
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


class TestGroups:
    def test_wagtail_groups_are_renamed(self):
        names = set(Group.objects.values_list("name", flat=True))

        assert {EDITORS_GROUP, ADMINISTRATORS_GROUP} <= names
        assert not names & {"Editors", "Moderators"}
        assert Workflow.objects.filter(name="Aprobación de administradores").exists()

    def test_roles_keep_wagtails_image_and_document_permissions(self):
        # Wagtail grants them by group name, so the renaming must run after it.
        for group_name in (EDITORS_GROUP, ADMINISTRATORS_GROUP):
            codenames = set(
                GroupCollectionPermission.objects.filter(
                    group__name=group_name
                ).values_list("permission__codename", flat=True)
            )
            assert {
                "add_image",
                "change_image",
                "add_document",
                "change_document",
            } <= codenames, group_name

    def test_renaming_keeps_users_and_permissions(self, make_user):
        editor = make_user("ana", EDITORS_GROUP)
        permissions_before = set(
            Group.objects.get(name=EDITORS_GROUP).permissions.values_list("pk")
        )

        roles_migration.backwards(apps, None)
        assert Group.objects.get(name="Editors").user_set.filter(pk=editor.pk).exists()
        roles_migration.forwards(apps, None)

        editors = Group.objects.get(name=EDITORS_GROUP)
        assert editors.user_set.filter(pk=editor.pk).exists()
        assert set(editors.permissions.values_list("pk")) == permissions_before

    def test_existing_names_are_not_overwritten(self):
        Group.objects.create(name="Editors")

        roles_migration.forwards(apps, None)

        assert Group.objects.filter(name="Editors").exists()
        assert Group.objects.filter(name=EDITORS_GROUP).count() == 1


class TestEditor:
    def test_edits_and_cannot_publish(self, make_user, content_page):
        permissions = content_page.permissions_for_user(make_user("ana", EDITORS_GROUP))

        assert permissions.can_edit()
        assert not permissions.can_publish()

    def test_is_not_an_administrator(self, make_user):
        assert not is_site_administrator(make_user("ana", EDITORS_GROUP))


class TestAdministrator:
    def test_publishes_and_deletes(self, make_user, content_page):
        permissions = content_page.permissions_for_user(
            make_user("administradora", ADMINISTRATORS_GROUP)
        )

        assert permissions.can_publish()
        assert permissions.can_delete()

    def test_manages_site_data_languages_and_users(self, make_user):
        administrator = make_user("administradora", ADMINISTRATORS_GROUP)

        for permission in (
            "orion_site_data.change_sitesettings",
            "orion_localization.change_languagesettings",
            "wagtailcore.add_locale",
            "auth.change_user",
            "orion_navigation.delete_menu",
        ):
            assert administrator.has_perm(permission), permission

    def test_does_not_reach_technical_settings(self, client, make_user):
        administrator = make_user("administradora", ADMINISTRATORS_GROUP)
        client.force_login(administrator)

        for permission in (
            "wagtailcore.change_site",
            "wagtailcore.add_collection",
            "wagtailcore.change_workflow",
            "auth.change_group",
        ):
            assert not administrator.has_perm(permission), permission
        assert client.get(reverse("wagtailsites:index")).status_code != 200

    def test_is_an_administrator(self, make_user, admin_user):
        assert is_site_administrator(make_user("administradora", ADMINISTRATORS_GROUP))
        assert is_site_administrator(admin_user)


class TestApproval:
    def test_administrator_approves_what_an_editor_submits(
        self, make_user, content_page
    ):
        editor = make_user("ana", EDITORS_GROUP)
        administrator = make_user("administradora", ADMINISTRATORS_GROUP)
        content_page.title = "Nosotros (revisado)"
        content_page.save_revision(user=editor)

        workflow_state = content_page.get_workflow().start(content_page, editor)
        task_state = workflow_state.current_task_state
        task = task_state.task.specific
        assert task.user_can_access_editor(content_page, administrator)
        assert not task.user_can_access_editor(content_page, editor)
        task.on_action(task_state, administrator, "approve")

        content_page.refresh_from_db()
        assert content_page.live
        assert content_page.title == "Nosotros (revisado)"


class TestSectionPermissions:
    def test_group_limited_to_a_section(self, make_user, home_page, content_page):
        news = ArticleIndexPage(title="Novedades", slug="novedades")
        home_page.add_child(instance=news)
        news.save_revision().publish()
        group = Group.objects.create(name="Prensa")
        group.permissions.add(Permission.objects.get(codename="access_admin"))
        GroupPagePermission.objects.create(
            group=group,
            page=news,
            permission=Permission.objects.get(
                content_type__app_label="wagtailcore", codename="change_page"
            ),
        )
        press = make_user("prensa", "Prensa")

        assert news.permissions_for_user(press).can_edit()
        assert not content_page.permissions_for_user(press).can_edit()
        assert not Page.get_first_root_node().permissions_for_user(press).can_edit()
