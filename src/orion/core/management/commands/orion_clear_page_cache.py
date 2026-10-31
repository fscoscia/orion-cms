from django.core.management.base import BaseCommand

from orion.core.cache import clear_page_cache


class Command(BaseCommand):
    help = "Empty the full-page cache; the next visit to each page builds it again."

    def handle(self, *args, **options):
        clear_page_cache()
        self.stdout.write("Page cache emptied.")
