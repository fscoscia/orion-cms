"""Clean uploaded SVG files: keep only drawing elements and attributes from an
allowlist, so an SVG cannot run scripts or load anything from elsewhere."""

import re
import xml.etree.ElementTree as ET  # noqa: S405 - only to build and write the result

from defusedxml import ElementTree as SafeET

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

ALLOWED_ELEMENTS = {
    "svg", "g", "defs", "symbol", "use", "title", "desc",
    "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "text", "tspan", "textPath",
    "linearGradient", "radialGradient", "stop", "pattern", "style",
    "clipPath", "mask", "filter", "marker",
    "feBlend", "feColorMatrix", "feComposite", "feFlood", "feGaussianBlur",
    "feMerge", "feMergeNode", "feOffset",
}  # fmt: skip

ALLOWED_ATTRIBUTES = {
    "id", "class", "viewBox", "width", "height", "x", "y", "x1", "y1", "x2", "y2",
    "cx", "cy", "r", "rx", "ry", "d", "points", "transform", "version",
    "preserveAspectRatio", "fill", "fill-opacity", "fill-rule", "clip-rule",
    "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
    "stroke-miterlimit", "stroke-dasharray", "stroke-dashoffset", "stroke-opacity",
    "opacity", "color", "display", "visibility", "clip-path", "mask", "filter",
    "marker-start", "marker-mid", "marker-end", "font-family", "font-size",
    "font-weight", "font-style", "text-anchor", "dominant-baseline",
    "letter-spacing", "dx", "dy", "offset", "stop-color", "stop-opacity",
    "gradientUnits", "gradientTransform", "spreadMethod", "fx", "fy",
    "patternUnits", "patternContentUnits", "patternTransform", "clipPathUnits",
    "maskUnits", "maskContentUnits", "markerWidth", "markerHeight", "refX", "refY",
    "orient", "stdDeviation", "in", "in2", "result", "mode", "operator", "values",
    "type", "flood-color", "flood-opacity", "href", "aria-label", "aria-hidden",
    "role", "style",
}  # fmt: skip

# Attributes that may point somewhere: only references inside the file stay.
LINK_ATTRIBUTES = {"href", "clip-path", "mask", "filter", "fill", "stroke",
                   "marker-start", "marker-mid", "marker-end", "style"}  # fmt: skip
EXTERNAL_URL = re.compile(r"url\(\s*['\"]?\s*(?!#)", re.IGNORECASE)
UNSAFE_CSS = re.compile(r"@import|expression\s*\(|javascript:", re.IGNORECASE)


class InvalidSVGError(ValueError):
    pass


def _local_name(name):
    return name.rsplit("}", 1)[-1]


def _is_safe_value(name, value):
    if name == "href":
        return value.strip().startswith("#")
    if name in LINK_ATTRIBUTES:
        return not EXTERNAL_URL.search(value) and not UNSAFE_CSS.search(value)
    return "javascript:" not in value.lower()


def _clean(element):
    for child in list(element):
        name = _local_name(child.tag) if isinstance(child.tag, str) else None
        is_unsafe_style = name == "style" and not _is_safe_value(
            "style", child.text or ""
        )
        if name not in ALLOWED_ELEMENTS or is_unsafe_style:
            element.remove(child)
        else:
            _clean(child)
    for name in list(element.attrib):
        local = _local_name(name)
        namespace = name[1:].split("}", 1)[0] if name.startswith("{") else ""
        allowed = namespace in ("", XLINK_NS) and local in ALLOWED_ATTRIBUTES
        if not allowed or not _is_safe_value(local, element.attrib[name]):
            del element.attrib[name]


def clean_svg(content):
    """Return the SVG with only allowed elements and attributes, as bytes.

    Raises InvalidSVGError if the content is not a safe, well-formed SVG document.
    """
    try:
        # Design tools add a DOCTYPE; entities and external references stay forbidden.
        root = SafeET.fromstring(
            content, forbid_dtd=False, forbid_entities=True, forbid_external=True
        )
    except Exception as error:
        raise InvalidSVGError(str(error)) from error
    if root.tag != f"{{{SVG_NS}}}svg":
        raise InvalidSVGError("The root element is not <svg>.")
    _clean(root)
    ET.register_namespace("", SVG_NS)
    ET.register_namespace("xlink", XLINK_NS)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
