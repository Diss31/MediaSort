"""Recursive discovery of image files."""

import os

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".jpe", ".tif", ".tiff",
    ".heic", ".heif",
    ".png", ".gif", ".bmp", ".webp",
}


def find_images(root):
    """Yields the path of every file under root with an image extension."""
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
                yield os.path.join(dirpath, name)
