"""The image library: large originals are reduced, SVG files are cleaned and the
renditions of every named size are generated when an image is saved."""

import io
import logging
import os
import threading

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.signals import request_finished, request_started
from django.db import close_old_connections, transaction
from django.db.models.signals import post_save, pre_save
from PIL import Image as PillowImage
from PIL import ImageOps
from wagtail.images import get_image_model
from wagtail.images.models import Filter

from orion.core.images import all_filter_specs
from orion.core.svg import clean_svg

logger = logging.getLogger(__name__)

# Whether this thread is answering a request: only then someone waits for the response.
_current = threading.local()

# Saving options for the formats a reduced original keeps.
SAVE_OPTIONS = {
    "JPEG": {"quality": 90},
    "WEBP": {"quality": 90},
    "AVIF": {"quality": 80},
}


def _is_new_file(image):
    file = image.file
    return bool(file) and not getattr(file, "_committed", True)


def _replace_file(image, content):
    name = os.path.basename(image.file.name)
    image.file = ContentFile(content, name=name)
    image._set_image_file_metadata()


def reduce_original(image):
    """Shrink a new bitmap original longer than ORION_IMAGE_MAX_DIMENSION on a side.

    Animated images keep their size: resizing them would drop the animation.
    """
    max_dimension = settings.ORION_IMAGE_MAX_DIMENSION
    image.file.seek(0)
    with PillowImage.open(image.file) as original:
        if getattr(original, "is_animated", False):
            return
        if max(original.size) <= max_dimension:
            return
        image_format = original.format
        reduced = ImageOps.exif_transpose(original)
        reduced.thumbnail((max_dimension, max_dimension))
        output = io.BytesIO()
        reduced.save(output, format=image_format, **SAVE_OPTIONS.get(image_format, {}))
    _replace_file(image, output.getvalue())
    image.width, image.height = reduced.size


def prepare_upload(sender, instance, **kwargs):
    if not _is_new_file(instance):
        return
    if instance.is_svg():
        instance.file.seek(0)
        _replace_file(instance, clean_svg(instance.file.read()))
    else:
        reduce_original(instance)


def generate_renditions(image):
    """Create the renditions of every named size that the image does not have yet."""
    existing = set(image.renditions.values_list("filter_spec", "focal_point_key"))
    # A new focal point needs new crops: Wagtail keys renditions by both.
    # Filters as Wagtail stores them (``preserve-svg`` resolved for the image).
    filters = {
        image.clean_filter_for_svg(Filter(spec)) for spec in all_filter_specs(image)
    }
    missing = [
        image_filter
        for image_filter in filters
        if (image_filter.spec, image_filter.get_cache_key(image)) not in existing
    ]
    if missing:
        image.get_renditions(*missing)
    return len(missing)


def _generate_in_thread(image_pk):
    try:
        image = get_image_model().objects.get(pk=image_pk)
        generate_renditions(image)
    except Exception:
        logger.exception("Could not generate the renditions of image %s", image_pk)
    finally:
        close_old_connections()


def _mark_request_started(**kwargs):
    _current.is_in_request = True


def _mark_request_finished(**kwargs):
    _current.is_in_request = False


def schedule_renditions(sender, instance, **kwargs):
    if kwargs.get("raw"):
        return

    def start():
        # A background thread dies with the process, so a command must not use one.
        is_in_request = getattr(_current, "is_in_request", False)
        if settings.ORION_IMAGE_RENDITIONS_IN_BACKGROUND and is_in_request:
            threading.Thread(
                target=_generate_in_thread, args=(instance.pk,), daemon=True
            ).start()
        else:
            generate_renditions(instance)

    transaction.on_commit(start)


def connect():
    image_model = get_image_model()
    pre_save.connect(prepare_upload, sender=image_model, dispatch_uid="orion_prepare")
    post_save.connect(
        schedule_renditions, sender=image_model, dispatch_uid="orion_renditions"
    )
    request_started.connect(_mark_request_started, dispatch_uid="orion_request_started")
    request_finished.connect(
        _mark_request_finished, dispatch_uid="orion_request_finished"
    )
