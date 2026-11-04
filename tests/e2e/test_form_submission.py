import pytest
from django.core.management import call_command

from orion.forms.models import FormPage

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.django_db(transaction=True, serialized_rollback=True),
]


class TestFormSubmission:
    def test_visitor_fills_and_submits_a_form(self, live_server_page, home_page):
        call_command("orion_create_example_forms")
        page = FormPage.objects.get(slug="formulario-de-contacto")

        live_server_page.goto(page.url)
        # Orion's antispam rejects a form shown less than ORION_FORMS_MIN_SECONDS ago.
        live_server_page.wait_for_timeout(3200)

        live_server_page.get_by_label("Nombre").fill("Ana López")
        live_server_page.get_by_label("Email").fill("ana@example.com")
        live_server_page.get_by_label("Mensaje").fill("Quisiera más información.")
        live_server_page.locator(
            ".orion-form__field--check input[type=checkbox]"
        ).check()
        live_server_page.click('form.orion-form button[type="submit"]')

        assert live_server_page.locator('[role="status"]').is_visible()
