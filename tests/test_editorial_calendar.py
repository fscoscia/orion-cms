import datetime

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from wagtail.models import GroupPagePermission, Revision

from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.pages.models import ArticleIndexPage, ContentPage

pytestmark = pytest.mark.django_db

CALENDAR = "orion_publication_calendar"


@pytest.fixture
def make_user(django_user_model):
    def _make(username, group_name):
        user = django_user_model.objects.create_user(username, password="x")
        user.groups.add(Group.objects.get(name=group_name))
        return user

    return _make


@pytest.fixture
def content_page(home_page):
    page = ContentPage(title="Nosotros", slug="nosotros")
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


def _at(days=0, hours=0, minutes=0):
    return timezone.now() + datetime.timedelta(days=days, hours=hours, minutes=minutes)


def _schedule(page, go_live_at, title=None):
    """Approve a change of the page to go live at ``go_live_at``."""
    page.title = title or page.title
    page.go_live_at = _at(days=1)
    revision = page.save_revision()
    revision.publish()
    # Moved afterwards: a past date would publish it at once instead of scheduling.
    Revision.objects.filter(pk=revision.pk).update(approved_go_live_at=go_live_at)
    return revision


def _expire(page, expire_at):
    type(page).objects.filter(pk=page.pk).update(expire_at=expire_at)


def _calendar(client, month=None):
    url = reverse(CALENDAR)
    return client.get(url, {"month": month} if month else {}).content.decode()


def _month(value):
    return f"{timezone.localtime(value):%Y-%m}"


class TestCalendar:
    def test_scheduled_publication_on_its_day(self, admin_client, content_page):
        go_live_at = _at(days=3)
        _schedule(content_page, go_live_at, title="Nosotros (nuevo)")

        html = _calendar(admin_client, _month(go_live_at))

        edit_url = reverse("wagtailadmin_pages:edit", args=[content_page.pk])
        assert "Nosotros (nuevo)" in html
        assert edit_url in html
        assert "orion-calendar__entry--publish" in html

    def test_expiry_on_its_day(self, admin_client, content_page):
        expire_at = _at(days=5)
        _expire(content_page, expire_at)

        html = _calendar(admin_client, _month(expire_at))

        assert "orion-calendar__entry--expire" in html
        assert "Nosotros" in html

    def test_other_months_do_not_show_it(self, admin_client, content_page):
        go_live_at = _at(days=3)
        _schedule(content_page, go_live_at)
        other = timezone.localtime(go_live_at) + datetime.timedelta(days=62)

        html = _calendar(admin_client, f"{other:%Y-%m}")

        assert "orion-calendar__entry--publish" not in html

    def test_only_pages_the_user_can_edit(
        self, client, django_user_model, home_page, content_page
    ):
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
        press = django_user_model.objects.create_user("prensa", password="x")
        press.groups.add(group)
        go_live_at = _at(days=3)
        _schedule(content_page, go_live_at, title="Nosotros (nuevo)")
        _schedule(news, go_live_at, title="Novedades (nuevo)")
        client.force_login(press)

        html = _calendar(client, _month(go_live_at))

        assert "Novedades (nuevo)" in html
        assert "Nosotros (nuevo)" not in html

    @pytest.mark.parametrize("month", ["2026-13", "nada", "0001-01", "9999-12"])
    def test_invalid_month_shows_the_current_one(self, admin_client, month):
        response = admin_client.get(reverse(CALENDAR), {"month": month})

        assert response.status_code == 200
        assert response.context["month"] == timezone.localdate().replace(day=1)

    def test_month_navigation(self, admin_client):
        response = admin_client.get(reverse(CALENDAR), {"month": "2026-12"})

        assert response.context["previous_month"] == "2026-11"
        assert response.context["next_month"] == "2027-01"
        assert 'href="?"' in response.content.decode()

    def test_late_entry_is_marked(self, client, make_user, content_page):
        _schedule(content_page, _at(hours=-2))
        client.force_login(make_user("ana", EDITORS_GROUP))

        html = _calendar(client, _month(_at(hours=-2)))

        assert "orion-calendar__entry--overdue" in html

    def test_menu_item(self, client, make_user, home_page):
        client.force_login(make_user("ana", EDITORS_GROUP))

        html = client.get(reverse("wagtailadmin_home")).content.decode()

        assert '"orion_calendar"' in html


class TestSchedulingWarning:
    WARNING = "orion-scheduling-warning"

    def _dashboard(self, client):
        return client.get(reverse("wagtailadmin_home")).content.decode()

    def test_two_hours_late_warns_administrators(self, client, make_user, content_page):
        _schedule(content_page, _at(hours=-2))
        client.force_login(make_user("jefa", ADMINISTRATORS_GROUP))

        assert self.WARNING in self._dashboard(client)
        assert self.WARNING in _calendar(client)

    def test_late_expiry_warns(self, admin_client, content_page):
        _expire(content_page, _at(hours=-2))

        assert self.WARNING in self._dashboard(admin_client)

    def test_ten_minutes_late_does_not_warn(self, admin_client, content_page):
        _schedule(content_page, _at(minutes=-10))

        assert self.WARNING not in self._dashboard(admin_client)

    def test_editors_do_not_see_it(self, client, make_user, content_page):
        _schedule(content_page, _at(hours=-2))
        client.force_login(make_user("ana", EDITORS_GROUP))

        assert self.WARNING not in self._dashboard(client)
        assert self.WARNING not in _calendar(client)

    def test_goes_away_once_the_task_runs(self, admin_client, content_page):
        _schedule(content_page, _at(hours=-2), title="Nosotros (nuevo)")

        call_command("publish_scheduled")

        content_page.refresh_from_db()
        assert content_page.title == "Nosotros (nuevo)"
        assert self.WARNING not in self._dashboard(admin_client)
