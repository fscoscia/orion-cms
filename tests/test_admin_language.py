import re

import pytest
from django.urls import reverse

from orion.editor.translations import (
    missing_wagtail_translations,
    redundant_orion_translations,
)

pytestmark = pytest.mark.django_db


def test_no_wagtail_phrase_is_left_untranslated():
    missing = missing_wagtail_translations("es")

    assert not missing, (
        "Wagtail phrases without Spanish (run scripts/missing_wagtail_translations.py):"
        f" {sorted(msgid for _domain, msgid in missing)}"
    )


def test_orion_catalog_does_not_override_translated_phrases():
    assert redundant_orion_translations("es") == set()


def test_login_labels_are_translated(client):
    html = client.get(reverse("wagtailadmin_login")).content.decode()
    labels = " ".join(re.findall(r"<label[^>]*>(.*?)</label>", html, re.S))

    assert "Nombre de usuario" in labels
    assert "Contraseña" in labels
    assert "Password" not in labels


def test_dashboard_search_is_translated(admin_client, home_page):
    html = admin_client.get(reverse("wagtailadmin_home")).content.decode()

    assert "Buscar en todas las páginas…" in html


def test_javascript_catalog_has_orions_phrases(admin_client):
    js = admin_client.get(reverse("wagtailadmin_javascript_catalog")).content.decode()

    assert "Buscar opciones\\u2026" in js or "Buscar opciones…" in js
