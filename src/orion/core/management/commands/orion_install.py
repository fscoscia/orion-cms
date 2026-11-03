from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import OperationalError, connections


class Command(BaseCommand):
    help = (
        "Set up a freshly created Orion site: check the database, migrate, create "
        "the administrator, confirm the base language and load example content."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help=(
                "Do not prompt when creating the administrator; use the "
                "DJANGO_SUPERUSER_* environment variables instead."
            ),
        )

    def handle(self, *args, **options):
        interactive = options["interactive"]
        verbosity = options["verbosity"]

        try:
            connections["default"].ensure_connection()
        except (ImproperlyConfigured, OperationalError) as error:
            raise CommandError(f"Database not ready: {error}") from error

        call_command("migrate", verbosity=verbosity)

        try:
            call_command(
                "createsuperuser", interactive=interactive, verbosity=verbosity
            )
        except CommandError as error:
            if "already taken" in str(error):
                self.stdout.write("Superuser already exists; skipping.")
            else:
                raise

        self.stdout.write(f"Base language: {settings.LANGUAGE_CODE}")

        call_command("orion_create_example_forms", verbosity=verbosity)

        self.stdout.write("Installation complete.")
