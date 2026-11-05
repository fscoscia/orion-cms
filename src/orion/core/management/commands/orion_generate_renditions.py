from django.core.management.base import BaseCommand
from wagtail.images import get_image_model

from orion.core.image_library import generate_renditions


class Command(BaseCommand):
    help = (
        "Generate the missing renditions of every named image size, including those "
        "whose file was lost from the storage."
    )

    def handle(self, *args, **options):
        created = failed = 0
        for image in get_image_model().objects.iterator():
            try:
                created += generate_renditions(image, repair=True)
            except Exception as error:  # noqa: BLE001 - one broken file must not stop the rest
                failed += 1
                self.stderr.write(f"{image.pk} {image.title}: {error}")
        self.stdout.write(
            f"Renditions created: {created}. Images that failed: {failed}."
        )
