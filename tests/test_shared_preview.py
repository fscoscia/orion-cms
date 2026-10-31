from datetime import timedelta

import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from django.utils import timezone

from orion.editor.models import PreviewLink
from orion.editor.roles import EDITORS_GROUP
from orion.pages.models import ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture
def content_page(home_page):
    page = ContentPage(title="Nosotros", slug="nosotros")
    home_page.add_child(instance=page)
    page.save_revision().publish()
    return page


@pytest.fixture
def editor(django_user_model):
    user = django_user_model.objects.create_user("ana", password="x")
    user.groups.add(Group.objects.get(name=EDITORS_GROUP))
    return user


def _draft(page, title):
    page.title = title
    page.save_revision()


def _link(page, **fields):
    fields.setdefault("expires_at", timezone.now() + timedelta(days=7))
    return PreviewLink.objects.create(page=page, **fields)


def _preview_url(link):
    return reverse("orion_shared_preview", args=[link.token])


class TestPublicView:
    def test_shows_the_latest_draft_without_a_session(self, client, content_page):
        _draft(content_page, "Nosotros (borrador)")
        link = _link(content_page)

        html = client.get(_preview_url(link)).content.decode()

        assert "Nosotros (borrador)" in html
        assert "orion/js/preview.js" in html
        assert (
            "Nosotros (borrador)" not in client.get(content_page.url).content.decode()
        )

    def test_later_edits_show_on_reload(self, client, content_page):
        link = _link(content_page)
        client.get(_preview_url(link))

        _draft(content_page, "Nosotros (segunda versión)")

        assert (
            "Nosotros (segunda versión)"
            in client.get(_preview_url(link)).content.decode()
        )

    def test_is_not_indexed_or_cached(self, client, content_page):
        response = client.get(_preview_url(_link(content_page)))

        assert response["X-Robots-Tag"] == "noindex, nofollow"
        assert "no-store" in response["Cache-Control"]
        assert response["Referrer-Policy"] == "no-referrer"

    def test_expired_link(self, client, content_page):
        link = _link(content_page, expires_at=timezone.now() - timedelta(minutes=1))

        assert client.get(_preview_url(link)).status_code == 404

    def test_unknown_token(self, client, content_page):
        _link(content_page)

        assert (
            client.get(reverse("orion_shared_preview", args=["x" * 43])).status_code
            == 404
        )

    def test_deleted_page(self, client, content_page):
        link = _link(content_page)
        token = link.token
        content_page.delete()

        assert (
            client.get(reverse("orion_shared_preview", args=[token])).status_code == 404
        )

    def test_tokens_are_long_and_different(self, content_page):
        first, second = _link(content_page), _link(content_page)

        assert len(first.token) >= 43
        assert first.token != second.token


class TestAdminScreen:
    def _url(self, page):
        return reverse("orion_preview_links", args=[page.pk])

    def test_editor_creates_a_link(self, client, editor, content_page):
        client.force_login(editor)

        response = client.post(self._url(content_page), {"days": "7"}, follow=True)

        link = PreviewLink.objects.get(page=content_page)
        assert link.created_by == editor
        assert (
            timedelta(days=6, hours=23)
            < link.expires_at - timezone.now()
            <= timedelta(days=7)
        )
        assert _preview_url(link) in response.content.decode()

    def test_invalid_expiry_is_rejected(self, client, editor, content_page):
        client.force_login(editor)

        response = client.post(self._url(content_page), {"days": "365"})

        assert response.status_code == 200
        assert not PreviewLink.objects.exists()

    def test_editor_revokes_a_link(self, client, editor, content_page):
        link = _link(content_page)
        client.force_login(editor)

        client.post(self._url(content_page), {"revoke": link.pk})

        assert not PreviewLink.objects.exists()
        assert client.get(_preview_url(link)).status_code == 404

    def test_expired_links_are_not_listed(self, client, editor, content_page):
        expired = _link(content_page, expires_at=timezone.now() - timedelta(days=1))
        client.force_login(editor)

        html = client.get(self._url(content_page)).content.decode()

        assert expired.token not in html

    def test_without_permission(self, client, django_user_model, content_page):
        group = Group.objects.create(name="Solo lectura")
        group.permissions.add(
            *Group.objects.get(name=EDITORS_GROUP).permissions.filter(
                codename="access_admin"
            )
        )
        reader = django_user_model.objects.create_user("beto", password="x")
        reader.groups.add(group)
        link = _link(content_page)
        client.force_login(reader)

        client.post(self._url(content_page), {"days": "7"})
        client.post(self._url(content_page), {"revoke": link.pk})
        page_html = client.get(self._url(content_page))

        assert PreviewLink.objects.count() == 1
        assert page_html.status_code != 200

    def test_page_header_offers_the_button(self, client, editor, content_page):
        client.force_login(editor)
        edit_url = reverse("wagtailadmin_pages:edit", args=[content_page.pk])

        assert self._url(content_page) in client.get(edit_url).content.decode()
