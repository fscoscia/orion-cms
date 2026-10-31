from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from django.urls import Resolver404, resolve, reverse
from django_otp import user_has_device
from django_otp.middleware import OTPMiddleware

# Admin URLs that stay open before the second factor is verified.
UNVERIFIED_URL_NAMES = {
    "wagtailadmin_login",
    "wagtailadmin_logout",
    "wagtailadmin_javascript_catalog",
    "wagtailadmin_sprite",
    "orion_admin_colors",
    "orion_2fa_verify",
    "orion_2fa_setup",
    "orion_2fa_backup_codes",
}


def has_admin_access(user):
    return user.is_authenticated and (
        user.is_superuser or user.has_perm("wagtailadmin.access_admin")
    )


class TwoFactorMiddleware(OTPMiddleware):
    """Requires a verified second factor for every admin page (ORION_2FA_REQUIRED).

    Goes after AuthenticationMiddleware. The public site is left alone.
    """

    async_capable = False

    def __call__(self, request):
        self._install_lazy_accessors(request)
        if self._needs_second_factor(request):
            name = (
                "orion_2fa_verify"
                if user_has_device(request.user)
                else "orion_2fa_setup"
            )
            return redirect(
                f"{reverse(name)}?{urlencode({'next': request.get_full_path()})}"
            )
        return self.get_response(request)

    @staticmethod
    def _needs_second_factor(request):
        if not getattr(settings, "ORION_2FA_REQUIRED", True):
            return False
        if not request.path.startswith(f"/{settings.ORION_ADMIN_PATH}"):
            return False
        user = request.user
        if not has_admin_access(user) or user.is_verified():
            return False
        try:
            return resolve(request.path_info).url_name not in UNVERIFIED_URL_NAMES
        except Resolver404:
            return False
