from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from orion.core.backups import BackupError, create_backup


class Command(BaseCommand):
    help = "Pack the database, media and private form attachments into one file."

    def add_arguments(self, parser):
        parser.add_argument("archive", help="Path of the backup file to create.")

    def handle(self, *args, **options):
        destination = Path(options["archive"])
        try:
            manifest = create_backup(destination)
        except BackupError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(
            f"Backup written to {destination} "
            f"({manifest['engine']}, {manifest['created_at']})."
        )
