from django.core.management.base import BaseCommand
from django.template.defaultfilters import filesizeformat
from wagtail.images import get_image_model
from wagtail.models import ReferenceIndex


class Command(BaseCommand):
    help = (
        "List the images that no page, snippet or setting uses. Nothing is deleted. "
        "Run rebuild_references_index first if the index may be out of date."
    )

    def handle(self, *args, **options):
        unused = [
            image
            for image in get_image_model().objects.order_by("created_at")
            if not ReferenceIndex.get_references_to(image).exists()
        ]
        sizes = {image.pk: image.get_file_size() or 0 for image in unused}
        for image in unused:
            self.stdout.write(
                f"{image.pk}\t{image.created_at:%Y-%m-%d}\t"
                f"{filesizeformat(sizes[image.pk])}\t{image.title}"
            )
        total = sum(sizes.values())
        self.stdout.write(f"Unused images: {len(unused)} ({filesizeformat(total)}).")
