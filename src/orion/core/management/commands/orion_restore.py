import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from orion.core.backups import (
    BackupError,
    ensure_engine_matches,
    read_manifest,
    restore_backup,
)


class Command(BaseCommand):
    help = (
        "Restore the database, media and private form attachments from a backup "
        "file. Replaces whatever is already on this server."
    )

    def add_arguments(self, parser):
        parser.add_argument("archive", help="Backup file created by orion_backup.")
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Do not prompt for confirmation; use for automated restores.",
        )

    def handle(self, *args, **options):
        archive_path = Path(options["archive"])
        try:
            manifest = read_manifest(archive_path)
            ensure_engine_matches(manifest)
        except BackupError as error:
            raise CommandError(str(error)) from error

        if options["interactive"]:
            if not sys.stdin.isatty():
                raise CommandError(
                    "Refusing to restore without a terminal attached; pass "
                    "--noinput to run it unattended."
                )
            confirm = input(
                "This replaces the database, media and form attachments on this "
                f"server with the contents of {archive_path}.\n"
                "Type 'yes' to continue, or anything else to cancel: "
            )
            if confirm != "yes":
                self.stdout.write("Restore cancelled.")
                return

        try:
            restore_backup(archive_path)
        except BackupError as error:
            raise CommandError(str(error)) from error
        self.stdout.write(f"Restored from {archive_path}.")
