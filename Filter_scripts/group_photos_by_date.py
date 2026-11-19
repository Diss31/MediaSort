"""
Recursively scans a folder tree for photos and groups them by date.

Files are grouped under "capture_time" when their real EXIF DateTimeOriginal
is readable. Everything else (no EXIF tag, or a format exifread can't parse
at all) falls back to "last_modified", grouped by file mtime instead.

See requirements.txt for dependencies.
"""

import argparse
import json
import os
import sys
from datetime import datetime

import exifread

# Formats exifread can actually parse EXIF from.
EXIF_CAPABLE_EXTENSIONS = {".jpg", ".jpeg", ".jpe", ".tif", ".tiff"}

IMAGE_EXTENSIONS = EXIF_CAPABLE_EXTENSIONS | {
    ".png", ".gif", ".bmp", ".webp", ".heic", ".heif",
}

EXIF_DATE_TAG = "EXIF DateTimeOriginal"
EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"


def find_images(root):
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
                yield os.path.join(dirpath, name)


def read_capture_date(path):
    """Returns a datetime from EXIF DateTimeOriginal, or None if unavailable."""
    try:
        with open(path, "rb") as f:
            tags = exifread.process_file(f, details=False, stop_tag=EXIF_DATE_TAG)
    except OSError:
        return None

    raw = tags.get(EXIF_DATE_TAG)
    if raw is None:
        return None

    try:
        return datetime.strptime(str(raw), EXIF_DATE_FORMAT)
    except ValueError:
        return None


def group_photos(root):
    capture_time = {}
    last_modified = {}

    for path in find_images(root):
        ext = os.path.splitext(path)[1].lower()
        capture_date = read_capture_date(path) if ext in EXIF_CAPABLE_EXTENSIONS else None

        if capture_date is not None:
            key = capture_date.date().isoformat()
            capture_time.setdefault(key, []).append(path)
        else:
            mtime = os.path.getmtime(path)
            key = datetime.fromtimestamp(mtime).date().isoformat()
            last_modified.setdefault(key, []).append((path, mtime))

    for paths in capture_time.values():
        paths.sort()
    for entries in last_modified.values():
        entries.sort(key=lambda entry: entry[1])

    return capture_time, last_modified


def build_report(capture_time, last_modified):
    return {
        "capture_time": {
            date: sorted(paths) for date, paths in sorted(capture_time.items())
        },
        "last_modified": {
            date: [path for path, _mtime in entries]
            for date, entries in sorted(last_modified.items())
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Group photos by real EXIF capture date into a report file."
    )
    parser.add_argument("root", help="Root folder to scan recursively for photos")
    parser.add_argument(
        "-o", "--output",
        default="photos_by_date.json",
        help="Path to the output JSON report (default: photos_by_date.json)",
    )
    args = parser.parse_args()

    capture_time, last_modified = group_photos(args.root)
    report = build_report(capture_time, last_modified)

    if os.path.exists(args.output):
        print(f"Warning: {args.output} already exists and will be overwritten.", file=sys.stderr)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    capture_count = sum(len(paths) for paths in capture_time.values())
    modified_count = sum(len(paths) for paths in last_modified.values())
    print(
        f"Scanned {capture_count + modified_count} image(s): "
        f"{capture_count} with capture time, {modified_count} falling back to last modified."
    )
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
