from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import filesizeformat

from orion.core.backups import BackupError, read_manifest


class Command(BaseCommand):
    help = "Show what a backup file contains, without restoring anything."

    def add_arguments(self, parser):
        parser.add_argument("archive", help="Backup file to inspect.")

    def handle(self, *args, **options):
        archive_path = Path(options["archive"])
        try:
            manifest = read_manifest(archive_path)
        except BackupError as error:
            raise CommandError(str(error)) from error
        sizes = manifest["sizes"]
        self.stdout.write(f"Engine: {manifest['engine']}")
        self.stdout.write(f"Created: {manifest['created_at']}")
        self.stdout.write(
            f"Orion {manifest['orion_version']}, Django {manifest['django_version']}"
        )
        self.stdout.write(f"Database: {filesizeformat(sizes['database'])}")
        self.stdout.write(f"Media: {filesizeformat(sizes['media'])}")
        self.stdout.write(f"Form attachments: {filesizeformat(sizes['forms_private'])}")
