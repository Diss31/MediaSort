"""Combined entry point: runs every filter on the same folder, one after the other.

Always produces every report; there is deliberately no way to run a single filter
here (the per-filter commands `mediasort-date` / `mediasort-geo` remain for the
container images). A failing filter does not stop the others: its error is
reported on stderr and the process exits non-zero once all have run.
"""

import argparse
import os
import sys

from mediasort.common.report import write_report
from mediasort.filters.date import grouping as date_grouping
from mediasort.filters.geo import grouping as geo_grouping

DATE_REPORT_NAME = "photos_by_date.json"
GEO_REPORT_NAME = "photos_by_location.json"


def run_date(root, output_dir, _args):
    output_path = os.path.join(output_dir, DATE_REPORT_NAME)
    capture_time, last_modified = date_grouping.group_photos(root)
    write_report(date_grouping.build_report(capture_time, last_modified), output_path)
    date_grouping.summarize(capture_time, last_modified, output_path)


def run_geo(root, output_dir, args):
    output_path = os.path.join(output_dir, GEO_REPORT_NAME)
    clusters, no_location = geo_grouping.group_photos(root, args.threshold)
    write_report(geo_grouping.build_report(clusters, no_location), output_path)
    geo_grouping.summarize(clusters, no_location, output_path)


FILTERS = [("date", run_date), ("geo", run_geo)]


def main():
    parser = argparse.ArgumentParser(
        description="Run every MediaSort filter on a folder and write one report per filter."
    )
    parser.add_argument("root", help="Root folder to scan recursively for photos")
    parser.add_argument(
        "-o", "--output",
        default=".",
        help=(
            "Folder the reports are written to, created if missing "
            f"(default: current folder). Files: {DATE_REPORT_NAME}, {GEO_REPORT_NAME}"
        ),
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=geo_grouping.DEFAULT_THRESHOLD_M,
        help=(
            "Geo filter: distance in metres below which two photos are considered "
            f"the same location (default: {geo_grouping.DEFAULT_THRESHOLD_M:g})"
        ),
    )
    args = parser.parse_args()

    if args.threshold <= 0:
        parser.error("--threshold must be greater than 0")

    try:
        os.makedirs(args.output, exist_ok=True)
    except OSError as error:
        parser.error(f"cannot create output folder {args.output}: {error}")

    failed = []
    for name, run in FILTERS:
        try:
            run(args.root, args.output, args)
        except Exception as error:
            print(f"Error: {name} filter failed: {error}", file=sys.stderr)
            failed.append(name)

    if failed:
        print(f"{len(failed)} filter(s) failed: {', '.join(failed)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
