"""
Recursively scans a folder tree for photos and groups them by the date they
were actually taken (EXIF DateTimeOriginal), not by file mtime/ctime.

Photos without a readable EXIF capture date are listed separately under
"no_exif", ordered by file mtime (best-effort, since it's all we have).

See requirements.txt for dependencies.
"""

import argparse
import json
import os
from datetime import datetime

import exifread

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".jpe", ".tif", ".tiff",
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
    by_date = {}
    no_exif = []

    for path in find_images(root):
        capture_date = read_capture_date(path)
        if capture_date is not None:
            key = capture_date.date().isoformat()
            by_date.setdefault(key, []).append(path)
        else:
            mtime = os.path.getmtime(path)
            no_exif.append((path, mtime))

    for paths in by_date.values():
        paths.sort()
    no_exif.sort(key=lambda entry: entry[1])

    return by_date, no_exif


def build_report(by_date, no_exif):
    return {
        "by_date": {date: sorted(paths) for date, paths in sorted(by_date.items())},
        "no_exif": [
            {
                "path": path,
                "mtime": datetime.fromtimestamp(mtime).isoformat(),
            }
            for path, mtime in no_exif
        ],
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

    by_date, no_exif = group_photos(args.root)
    report = build_report(by_date, no_exif)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    total = sum(len(paths) for paths in by_date.values()) + len(no_exif)
    print(f"Scanned {total} image(s): {len(by_date)} date group(s), {len(no_exif)} without EXIF date.")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()
