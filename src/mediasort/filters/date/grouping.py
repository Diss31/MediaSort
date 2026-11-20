"""
Recursively scans a folder tree for photos and groups them by date.

Files are grouped under "capture_time" when their real EXIF DateTimeOriginal
is readable (HEIC/HEIF best-effort). Everything else (no EXIF tag, or a format
exifread can't parse at all) falls back to "last_modified", grouped by file
mtime instead.

Dependencies are declared in the root pyproject.toml.
"""

import argparse
import os
from datetime import datetime

from mediasort.common.exif import read_exif_tags
from mediasort.common.files import find_images
from mediasort.common.report import write_report

EXIF_DATE_TAG = "EXIF DateTimeOriginal"
EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"


def read_capture_date(path):
    """Returns a datetime from EXIF DateTimeOriginal, or None if unavailable."""
    tags = read_exif_tags(path, stop_tag=EXIF_DATE_TAG)
    if tags is None:
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
        capture_date = read_capture_date(path)

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
        "filter": "date",
        "groups": {
            "capture_time": {
                date: sorted(paths) for date, paths in sorted(capture_time.items())
            },
            "last_modified": {
                date: [path for path, _mtime in entries]
                for date, entries in sorted(last_modified.items())
            },
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
    write_report(report, args.output)
    summarize(capture_time, last_modified, args.output)


def summarize(capture_time, last_modified, output_path):
    """Prints the scan counts and where the report was written."""
    capture_count = sum(len(paths) for paths in capture_time.values())
    modified_count = sum(len(paths) for paths in last_modified.values())
    print(
        f"Scanned {capture_count + modified_count} image(s): "
        f"{capture_count} with capture time, {modified_count} falling back to last modified."
    )
    print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
