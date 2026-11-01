from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMessage
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods

from orion.editor.roles import is_site_administrator
from orion.integrations.status import (
    get_email_settings,
    get_email_state,
    get_map_provider,
)


class TestEmailForm(forms.Form):
    recipient = forms.EmailField(label=_("Send a test email to"))


@require_http_methods(["GET", "POST"])
def integrations(request):
    """Each integration's state, a test of the email and how to activate them."""
    if not is_site_administrator(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = TestEmailForm(request.POST)
        if form.is_valid():
            recipient = form.cleaned_data["recipient"]
            message = EmailMessage(
                subject=gettext("Test email from %(site)s")
                % {"site": request.get_host()},
                body=gettext(
                    "This is a test from the site's Integrations screen. If you read "
                    "it, the site's emails go out."
                ),
                to=[recipient],
            )
            try:
                message.send()
            except Exception as error:  # noqa: BLE001 - shown to the administrator
                messages.error(
                    request,
                    _("The test email could not be sent: %(error)s") % {"error": error},
                )
            else:
                messages.success(
                    request,
                    _("Test email sent to %(recipient)s.") % {"recipient": recipient},
                )
            return redirect("orion_integrations")
    else:
        form = TestEmailForm(initial={"recipient": request.user.email})
    return TemplateResponse(
        request,
        "orion/integrations/integrations.html",
        {
            "form": form,
            "email": get_email_state(),
            "email_settings": get_email_settings(),
            "map_provider": get_map_provider(),
            "is_debug": settings.DEBUG,
        },
    )
