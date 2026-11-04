from django.core.management.base import BaseCommand

from orion.core.conventions import check_project


class Command(BaseCommand):
    help = (
        "Report hardcoded text in templates, images without alt text, and incomplete "
        "translations. Informational only: nothing is changed and it always exits 0."
    )

    def handle(self, *args, **options):
        findings = check_project()
        if not findings:
            self.stdout.write("No findings.")
            return
        for finding in findings:
            self.stdout.write(f"{finding.path}:{finding.line}: {finding.message}")
        self.stdout.write(f"Findings: {len(findings)}.")
