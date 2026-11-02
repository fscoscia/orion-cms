"""Whether an uploaded file's content matches its extension."""

OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ZIP = b"PK\x03\x04"

SIGNATURES = {
    "pdf": (b"%PDF",),
    "doc": (OLE,),
    "xls": (OLE,),
    "ppt": (OLE,),
    # Office Open XML and OpenDocument files are zip archives.
    "docx": (ZIP,),
    "xlsx": (ZIP,),
    "pptx": (ZIP,),
    "odt": (ZIP,),
    "ods": (ZIP,),
    "odp": (ZIP,),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "png": (b"\x89PNG\r\n\x1a\n",),
}
TEXT_EXTENSIONS = {"txt", "csv"}
TEXT_SAMPLE_SIZE = 8192


def _read_start(file, size):
    position = file.tell() if hasattr(file, "tell") else 0
    file.seek(0)
    start = file.read(size)
    file.seek(position)
    return start


def matches_extension(file, extension):
    """True when the content looks like the extension says; unknown ones pass.

    Reads only the first bytes: enough to catch a program renamed to ``.pdf``.
    """
    extension = extension.lower().lstrip(".")
    if extension in TEXT_EXTENSIONS:
        return b"\x00" not in _read_start(file, TEXT_SAMPLE_SIZE)
    signatures = SIGNATURES.get(extension)
    if signatures is None:
        return True
    start = _read_start(file, max(len(signature) for signature in signatures))
    return any(start.startswith(signature) for signature in signatures)
