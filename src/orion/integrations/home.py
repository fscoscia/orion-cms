from django.conf import settings
from wagtail.admin.ui.components import Component

from orion.editor.roles import is_site_administrator
from orion.integrations.status import FAILING, get_email_state


class EmailWarningPanel(Component):
    """Tells administrators that the site's emails are not going out."""

    name = "orion_email_warning"
    template_name = "orion/integrations/email_warning.html"
    order = 6

    def get_context_data(self, parent_context):
        # Imported here: page models load after this app's hooks.
        from orion.forms.models import EmailNotice, FormSubmission

        context = super().get_context_data(parent_context)
        if not is_site_administrator(parent_context["request"].user):
            return context
        context["is_not_configured"] = not settings.EMAIL_HOST and not settings.DEBUG
        context["is_failing"] = (
            bool(settings.EMAIL_HOST) and get_email_state()["state"] == FAILING
        )
        context["pending_count"] = FormSubmission.objects.filter(
            email_notice=EmailNotice.PENDING
        ).count()
        return context
