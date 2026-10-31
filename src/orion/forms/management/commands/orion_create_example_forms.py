from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from wagtail.models import Locale, Page, Site

from orion.forms.models import FormField, FormPage

EXAMPLES = [
    {
        "title": "Contacto",
        "slug": "formulario-de-contacto",
        "intro": "<p>Escribinos y te respondemos a la brevedad.</p>",
        "subject": "Nueva consulta desde el sitio",
        "fields": [
            ("Nombre", "singleline", True),
            ("Email", "email", True),
            ("Teléfono", "phone", False),
            ("Mensaje", "multiline", True),
        ],
    },
    {
        "title": "Trabajá con nosotros",
        "slug": "trabaja-con-nosotros",
        "intro": "<p>Dejanos tus datos y tu CV.</p>",
        "subject": "Nueva postulación desde el sitio",
        "fields": [
            ("Nombre", "singleline", True),
            ("Email", "email", True),
            ("Teléfono", "phone", False),
            ("CV", "file", True),
            ("Comentarios", "multiline", False),
        ],
    },
]


class Command(BaseCommand):
    help = "Create the example forms (contact and job application) if missing."

    def handle(self, *args, **options):
        site = Site.objects.filter(is_default_site=True).first()
        if site is None:
            raise CommandError("There is no default site.")
        home = site.root_page.get_translation_or_none(Locale.get_default())
        home = (home or site.root_page).specific
        for example in EXAMPLES:
            if Page.objects.child_of(home).filter(slug=example["slug"]).exists():
                self.stdout.write(f"Already exists: {example['title']}")
                continue
            page = FormPage(
                title=example["title"],
                slug=example["slug"],
                intro=example["intro"],
                subject=example["subject"],
                to_address=settings.DEFAULT_FROM_EMAIL,
                form_fields=[
                    FormField(label=label, field_type=field_type, required=required)
                    for label, field_type, required in example["fields"]
                ],
            )
            home.add_child(instance=page)
            page.save_revision().publish()
            self.stdout.write(f"Created: {example['title']} ({page.url})")
