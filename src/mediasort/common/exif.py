"""Raw EXIF tag reading. Interpreting the tags is left to each filter."""

import os

import exifread
from exifread.tags import DEFAULT_STOP_TAG

# Formats exifread can parse EXIF from. HEIC/HEIF support is best-effort: it
# succeeds on many files but not all, and failures are reported as None.
EXIF_CAPABLE_EXTENSIONS = {
    ".jpg", ".jpeg", ".jpe", ".tif", ".tiff", ".heic", ".heif",
}


def read_exif_tags(path, stop_tag=DEFAULT_STOP_TAG):
    """Returns exifread's tag dict for path, or None if the format can't carry
    EXIF or the file can't be read.

    stop_tag makes exifread stop parsing once that tag is reached, which is
    faster when a filter only needs one tag.
    """
    if os.path.splitext(path)[1].lower() not in EXIF_CAPABLE_EXTENSIONS:
        return None

    try:
        with open(path, "rb") as f:
            return exifread.process_file(f, details=False, stop_tag=stop_tag)
    except (OSError, ValueError):
        return None
