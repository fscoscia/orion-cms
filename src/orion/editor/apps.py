from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EditorConfig(AppConfig):
    name = "orion.editor"
    label = "orion_editor"
    verbose_name = _("Editor experience")

    def ready(self):
        from orion.editor import checks  # noqa: F401
