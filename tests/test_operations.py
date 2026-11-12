import ast
from pathlib import Path

import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models.signals import post_delete
from wagtail.contrib.redirects.models import Redirect
from wagtail.models import Locale, Page, PageLogEntry

from orion import operations
from orion.editor.roles import ADMINISTRATORS_GROUP, EDITORS_GROUP
from orion.operations.errors import RevisionConflictError
from orion.operations.richtext import clean_rich_text
from orion.pages.models import ContentPage, HomePage
from orion.site_data.models import SiteSettings, SiteTexts

pytestmark = pytest.mark.django_db

TEXT_BLOCK = "text"


@pytest.fixture
def make_user(django_user_model):
    def _make(username, group_name=None, **extra):
        user = django_user_model.objects.create_user(username, password="x", **extra)
        if group_name:
            user.groups.add(Group.objects.get(name=group_name))
        return user

    return _make


@pytest.fixture
def editor(make_user):
    return make_user("editor", EDITORS_GROUP)


@pytest.fixture
def administrator(make_user):
    return make_user("administrator", ADMINISTRATORS_GROUP)


@pytest.fixture
def published_page(home_page):
    page = home_page.add_child(instance=ContentPage(title="Nosotros", slug="nosotros"))
    page.save_revision().publish()
    return page


def _text(html):
    return [{"type": TEXT_BLOCK, "value": {"body": html}}]


def _body_html(page):
    revision = page.get_latest_revision_as_object()
    return revision.body.get_prep_value()[0]["value"]["body"]


# The layer knows nothing of the MCP


def test_the_layer_does_not_import_the_mcp():
    folder = Path(operations.__file__).parent
    for path in folder.glob("*.py"):
        for node in ast.walk(ast.parse(path.read_text())):
            names = []
            if isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            elif isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            assert not [name for name in names if name.startswith("orion.mcp")], path


def test_an_inactive_user_cannot_operate(home_page, make_user):
    inactive = make_user("gone", EDITORS_GROUP, is_active=False)

    with pytest.raises(PermissionDenied):
        operations.create_page_draft(
            inactive, home_page, ContentPage, {"title": "Hola"}
        )


# Rich text


@pytest.mark.parametrize(
    ("html", "absent"),
    [
        ("<p>Hola<script>alert(1)</script></p>", "<script"),
        ('<p><b onclick="x()">negrita</b></p>', "onclick"),
        ('<p style="color:red">rojo</p>', "style="),
        ('<p><a href="javascript:alert(1)">enlace</a></p>', "javascript:"),
    ],
)
def test_rich_text_loses_what_the_field_does_not_allow(html, absent):
    cleaned = clean_rich_text(html, ["bold", "italic", "link"])

    assert absent not in cleaned
    assert "<p" in cleaned


def test_rich_text_keeps_the_allowed_features():
    cleaned = clean_rich_text(
        '<p><b>negrita</b> y <a href="https://example.com/">enlace</a></p>',
        ["bold", "italic", "link"],
    )

    assert "<b>negrita</b>" in cleaned
    assert 'href="https://example.com/"' in cleaned


def test_rich_text_with_broken_markup_is_a_validation_error():
    with pytest.raises(ValidationError):
        clean_rich_text('<p>a<img src="x"></p>', ["bold"])


# Create a draft


def test_an_editor_creates_a_draft(editor, home_page):
    page = operations.create_page_draft(
        editor, home_page, ContentPage, {"title": "Servicios"}
    )

    assert page.live is False
    assert page.slug == "servicios"
    assert page.owner == editor
    assert page.get_latest_revision().user == editor
    assert page.latest_revision_id is not None
    assert PageLogEntry.objects.filter(
        page=page, action="wagtail.create", user=editor
    ).exists()


def test_a_user_without_permission_cannot_create(home_page, make_user):
    nobody = make_user("nobody")

    with pytest.raises(PermissionDenied):
        operations.create_page_draft(nobody, home_page, ContentPage, {"title": "X"})

    assert not Page.objects.filter(title="X").exists()


def test_a_page_type_not_allowed_under_the_parent_is_rejected(editor, home_page):
    with pytest.raises(ValidationError):
        operations.create_page_draft(editor, home_page, HomePage, {"title": "Otra"})


@pytest.mark.parametrize("field", ["live", "owner", "path", "depth", "unknown"])
def test_internal_fields_cannot_be_written(editor, home_page, field):
    with pytest.raises(ValidationError):
        operations.create_page_draft(
            editor, home_page, ContentPage, {"title": "X", field: 1}
        )


def test_a_page_needs_a_title(editor, home_page):
    with pytest.raises(ValidationError):
        operations.create_page_draft(editor, home_page, ContentPage, {})


def test_a_repeated_slug_is_rejected_and_creates_nothing(
    editor, home_page, published_page
):
    before = Page.objects.count()

    with pytest.raises(ValidationError):
        operations.create_page_draft(
            editor, home_page, ContentPage, {"title": "Otra", "slug": "nosotros"}
        )

    assert Page.objects.count() == before


def test_a_draft_can_be_created_with_a_body(editor, home_page):
    page = operations.create_page_draft(
        editor,
        home_page,
        ContentPage,
        {"title": "Con cuerpo", "body": _text("<p>Hola</p>")},
    )

    assert "Hola" in _body_html(page)


# Update a draft


def test_updating_creates_a_revision_and_keeps_the_published_version(
    editor, published_page
):
    revision = published_page.latest_revision_id

    updated = operations.update_page_draft(
        editor, published_page, {"title": "Quiénes somos"}, revision
    )

    assert updated.latest_revision_id != revision
    assert updated.get_latest_revision().user == editor
    assert updated.live is True
    assert updated.title == "Nosotros"  # what visitors see did not change
    assert updated.has_unpublished_changes is True
    assert updated.get_latest_revision_as_object().title == "Quiénes somos"


def test_a_stale_revision_is_a_conflict_and_saves_nothing(editor, published_page):
    stale = published_page.latest_revision_id
    operations.update_page_draft(editor, published_page, {"title": "Uno"}, stale)

    with pytest.raises(RevisionConflictError):
        operations.update_page_draft(editor, published_page, {"title": "Dos"}, stale)

    latest = Page.objects.get(pk=published_page.pk).get_latest_revision_as_object()
    assert latest.title == "Uno"


def test_scripts_in_the_body_do_not_reach_the_revision(editor, published_page):
    operations.update_page_draft(
        editor,
        published_page,
        {"body": _text("<p>Hola<script>alert(1)</script></p>")},
        published_page.latest_revision_id,
    )

    page = Page.objects.get(pk=published_page.pk)
    assert "<script" not in _body_html(page)


def test_an_unknown_block_is_a_validation_error(editor, published_page):
    with pytest.raises(ValidationError):
        operations.update_page_draft(
            editor,
            published_page,
            {"body": [{"type": "no_such_block", "value": {}}]},
            published_page.latest_revision_id,
        )


def test_a_page_locked_by_someone_else_cannot_be_edited(
    editor, administrator, published_page
):
    published_page.locked = True
    published_page.locked_by = administrator
    published_page.save()

    with pytest.raises(PermissionDenied):
        operations.update_page_draft(
            editor, published_page, {"title": "X"}, published_page.latest_revision_id
        )


def test_internal_fields_cannot_be_updated(editor, published_page):
    with pytest.raises(ValidationError):
        operations.update_page_draft(
            editor, published_page, {"live": False}, published_page.latest_revision_id
        )


# Redirects


def test_an_administrator_creates_a_redirect(administrator):
    redirect = operations.create_redirect(
        administrator,
        {"old_path": "/viejo", "redirect_link": "https://example.com/nuevo/"},
    )

    assert redirect.old_path == "/viejo"
    assert redirect.is_permanent is True


def test_an_editor_cannot_manage_redirects(editor):
    with pytest.raises(PermissionDenied):
        operations.create_redirect(
            editor,
            {"old_path": "/viejo", "redirect_link": "https://example.com/nuevo/"},
        )

    assert not Redirect.objects.exists()


def test_a_redirect_to_itself_is_rejected(administrator):
    with pytest.raises(ValidationError):
        operations.create_redirect(
            administrator, {"old_path": "/a", "redirect_link": "http://localhost/a"}
        )


def test_a_repeated_origin_is_rejected(administrator):
    operations.create_redirect(
        administrator, {"old_path": "/a", "redirect_link": "https://example.com/b"}
    )

    with pytest.raises(ValidationError):
        operations.create_redirect(
            administrator, {"old_path": "/a", "redirect_link": "https://example.com/c"}
        )


@pytest.mark.parametrize(
    "link", ["javascript:alert(1)", "ftp://x.example/", "nuevo", "/nuevo/"]
)
def test_a_link_that_is_not_http_or_a_path_is_rejected(administrator, link):
    with pytest.raises(ValidationError):
        operations.create_redirect(
            administrator, {"old_path": "/a", "redirect_link": link}
        )


def test_a_redirect_to_a_page(administrator, published_page):
    redirect = operations.create_redirect(
        administrator, {"old_path": "/vieja", "redirect_page": published_page.pk}
    )

    assert redirect.redirect_page_id == published_page.pk


def test_a_redirect_is_updated(administrator):
    redirect = operations.create_redirect(
        administrator, {"old_path": "/a", "redirect_link": "https://example.com/b"}
    )

    operations.update_redirect(
        administrator,
        redirect,
        {"redirect_link": "https://example.com/c", "is_permanent": False},
    )

    redirect.refresh_from_db()
    assert redirect.redirect_link == "https://example.com/c"
    assert redirect.is_permanent is False


# Site data and texts


def test_an_editor_updates_the_site_texts(editor):
    texts = operations.update_site_texts(editor, "es", {"tagline": "Cuidamos tu sitio"})

    assert SiteTexts.objects.get(pk=texts.pk).tagline == "Cuidamos tu sitio"


def test_site_texts_of_an_unknown_language_are_rejected(editor):
    with pytest.raises(ValidationError):
        operations.update_site_texts(editor, "zz", {"tagline": "x"})


def test_an_editor_cannot_update_the_site_data(editor):
    with pytest.raises(PermissionDenied):
        operations.update_site_settings(editor, {"phone": "123"})


def test_an_administrator_updates_the_site_data(administrator):
    operations.update_site_settings(administrator, {"phone": "+595 21 000 000"})

    assert SiteSettings.objects.get().phone == "+595 21 000 000"


def test_site_data_rejects_unknown_fields(administrator):
    with pytest.raises(ValidationError):
        operations.update_site_settings(administrator, {"nope": 1})


# Operations never publish or delete


def test_no_operation_publishes_or_deletes(
    editor, administrator, home_page, published_page
):
    deleted = []

    def count(sender, **kwargs):
        deleted.append(sender)

    post_delete.connect(count, dispatch_uid="test_operations_deletions")
    live_before = set(Page.objects.filter(live=True).values_list("pk", flat=True))
    redirects_before = Redirect.objects.count()
    try:
        draft = operations.create_page_draft(
            editor, home_page, ContentPage, {"title": "Nueva"}
        )
        operations.update_page_draft(
            editor, draft, {"title": "Nueva 2"}, draft.latest_revision_id
        )
        operations.update_page_draft(
            editor,
            published_page,
            {"title": "Nosotros 2"},
            published_page.latest_revision_id,
        )
        redirect = operations.create_redirect(
            administrator, {"old_path": "/a", "redirect_link": "https://example.com/b"}
        )
        operations.update_redirect(
            administrator, redirect, {"redirect_link": "https://example.com/c"}
        )
        operations.update_site_settings(administrator, {"phone": "1"})
        operations.update_site_texts(editor, "es", {"tagline": "t"})
    finally:
        post_delete.disconnect(dispatch_uid="test_operations_deletions")

    assert (
        set(Page.objects.filter(live=True).values_list("pk", flat=True)) == live_before
    )
    assert Page.objects.get(pk=draft.pk).live is False
    assert Redirect.objects.count() == redirects_before + 1
    assert deleted == []


def test_page_changes_are_attributed_to_the_acting_user(editor, published_page):
    operations.update_page_draft(
        editor, published_page, {"title": "Cambio"}, published_page.latest_revision_id
    )

    page = Page.objects.get(pk=published_page.pk)
    assert page.get_latest_revision().user == editor
    assert PageLogEntry.objects.filter(
        page=page, action="wagtail.edit", user=editor
    ).exists()


def test_locales_exist_for_the_site_texts_tests():
    assert Locale.objects.filter(language_code="es").exists()
