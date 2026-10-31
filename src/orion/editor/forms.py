from django.utils.translation import gettext_lazy as _
from wagtail.admin.forms.auth import LoginForm as WagtailLoginForm


class LoginForm(WagtailLoginForm):
    """Wagtail's login form with translated labels.

    Wagtail leaves the password field without a label, so Django shows its name,
    "Password", in every language.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = _("Password")
        self.fields["remember"].label = _("Remember me")
