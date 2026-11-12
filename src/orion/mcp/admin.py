"""The admin screen where Administrators make and revoke MCP API keys."""

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST

from orion.editor.roles import is_site_administrator
from orion.mcp.models import ApiKey, Scope


def _require_administrator(request):
    if not is_site_administrator(request.user):
        raise PermissionDenied


class ApiKeyForm(forms.ModelForm):
    class Meta:
        model = ApiKey
        fields = ["name", "user", "scope", "expires_at"]
        widgets = {
            "expires_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            )
        }
        help_texts = {
            "user": _(
                "The key acts as this account and has its permissions at most. "
                "Choose a dedicated Editor, never a superuser."
            ),
            "scope": _(
                "Read only never changes anything; drafts also saves drafts; full "
                "also changes redirects and site data at once, and only a "
                "superuser can create it."
            ),
            "expires_at": _(
                "Recommended: a key that expires limits the harm of a leak."
            ),
        }

    def __init__(self, *args, creator=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not (creator and creator.is_superuser):
            self.fields["scope"].choices = [
                choice
                for choice in self.fields["scope"].choices
                if choice[0] != Scope.FULL
            ]
        self.fields["user"].queryset = (
            get_user_model()
            .objects.filter(is_active=True, is_superuser=False)
            .order_by(get_user_model().USERNAME_FIELD)
        )
        self.fields["expires_at"].input_formats = ["%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]


def keys_list(request):
    _require_administrator(request)
    keys = ApiKey.objects.select_related("user", "created_by")
    return TemplateResponse(
        request,
        "orion/mcp/keys.html",
        {
            "keys": keys,
            "endpoint_enabled": settings.ORION_MCP_ENDPOINT,
            "endpoint_url": request.build_absolute_uri("/_mcp/"),
        },
    )


@require_http_methods(["GET", "POST"])
def key_new(request):
    _require_administrator(request)
    form = ApiKeyForm(request.POST or None, creator=request.user)
    if request.method == "POST" and form.is_valid():
        key, token = ApiKey.issue(
            name=form.cleaned_data["name"],
            scope=form.cleaned_data["scope"],
            user=form.cleaned_data["user"],
            created_by=request.user,
            expires_at=form.cleaned_data["expires_at"],
        )
        # The token is shown here, in the answer to the POST, and kept nowhere else.
        response = TemplateResponse(
            request,
            "orion/mcp/key_created.html",
            {
                "key": key,
                "token": token,
                "endpoint_url": request.build_absolute_uri("/_mcp/"),
            },
        )
        response["Cache-Control"] = "no-store"
        return response
    return TemplateResponse(request, "orion/mcp/key_form.html", {"form": form})


@require_POST
def key_revoke(request, pk):
    _require_administrator(request)
    key = get_object_or_404(ApiKey, pk=pk)
    key.revoke()
    messages.success(request, _("The key “%(name)s” was revoked.") % {"name": key.name})
    return redirect("orion_mcp_keys")
