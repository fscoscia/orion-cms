from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.contrib.redirects.models import Redirect

from orion.seo.models import NotFoundPath


@receiver(post_save, sender=Redirect, dispatch_uid="orion_seo_redirected_path")
def forget_redirected_path(sender, instance, **kwargs):
    """A path with a redirect no longer answers 404."""
    # Wagtail stores the path without its trailing slash; the monitor, as requested.
    old_path = instance.old_path.rstrip("/")
    paths = NotFoundPath.objects.filter(path__in=[old_path, f"{old_path}/"])
    if instance.site_id:
        paths = paths.filter(site_id=instance.site_id)
    paths.delete()
