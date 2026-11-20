"""Build a prioritized JSON file-tree plan from filter report files."""

import argparse
import json
import sys
from pathlib import Path

import yaml

from mediasort.common.report import validate_report

SUPPORTED_FILTERS = {"date", "geo"}
DATE_GROUPS = {"capture_time", "last_modified"}
GEO_GROUPS = {"locations", "no_location"}


def load_config(config_path):
    config_path = Path(config_path)
    with config_path.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if not isinstance(config, dict) or set(config) != {"filter_order", "reports_location"}:
        raise ValueError(
            "configuration must contain exactly 'filter_order' and 'reports_location'"
        )

    filter_order = config["filter_order"]
    if (
        not isinstance(filter_order, list)
        or not filter_order
        or any(not isinstance(name, str) or name not in SUPPORTED_FILTERS for name in filter_order)
    ):
        raise ValueError("'filter_order' must be a non-empty list containing supported filters")
    if len(set(filter_order)) != len(filter_order):
        raise ValueError("'filter_order' must not contain duplicates")

    reports_location = config["reports_location"]
    if not isinstance(reports_location, dict) or set(reports_location) != set(filter_order):
        raise ValueError(
            "'reports_location' must map each filter in 'filter_order' to one report path"
        )
    for name, report_path in reports_location.items():
        if not isinstance(report_path, str) or not report_path:
            raise ValueError(f"report path for {name!r} must be a non-empty string")

    config_dir = config_path.resolve().parent
    resolved_reports = {
        name: (config_dir / report_path).resolve()
        for name, report_path in reports_location.items()
    }
    return filter_order, resolved_reports


def _collect_named_buckets(node, label):
    if not isinstance(node, dict):
        raise ValueError(f"{label} must map group names directly to file lists")
    paths = {}
    for name, files in node.items():
        if not isinstance(files, list):
            raise ValueError(f"{label}.{name} must be a list of file paths")
        for file_path in files:
            paths[file_path] = (name,)
    return paths


def _filter_group_paths(filter_name, report):
    groups = report["groups"]
    if filter_name == "date":
        if set(groups) != DATE_GROUPS:
            raise ValueError("date report groups must contain 'capture_time' and 'last_modified'")
        paths = _collect_named_buckets(groups["capture_time"], "capture_time")
        for path in _collect_named_buckets(groups["last_modified"], "last_modified"):
            if path in paths:
                raise ValueError(f"file path {path!r} appears more than once in date groups")
            paths[path] = ("unknown",)
        return paths

    if filter_name == "geo":
        if set(groups) != GEO_GROUPS:
            raise ValueError("geo report groups must contain 'locations' and 'no_location'")
        paths = _collect_named_buckets(groups["locations"], "locations")
        no_location = groups["no_location"]
        if not isinstance(no_location, list):
            raise ValueError("no_location must be a list of file paths")
        for path in no_location:
            if path in paths:
                raise ValueError(f"file path {path!r} appears more than once in geo groups")
            paths[path] = ("unknown",)
        return paths

    raise ValueError(f"unsupported filter {filter_name!r}")


def build_plan(filter_order, reports):
    """Combines validated filter reports into a nested directory tree."""
    report_groups = {}
    for filter_name in filter_order:
        report = validate_report(reports[filter_name], expected_filter=filter_name)
        report_groups[filter_name] = _filter_group_paths(filter_name, report)

    reference_filter = filter_order[0]
    reference_paths = set(report_groups[reference_filter])
    for filter_name in filter_order[1:]:
        paths = set(report_groups[filter_name])
        if paths != reference_paths:
            missing = sorted(reference_paths - paths)
            extra = sorted(paths - reference_paths)
            details = []
            if missing:
                details.append(f"missing {missing[0]!r}")
            if extra:
                details.append(f"unexpected {extra[0]!r}")
            raise ValueError(
                f"{filter_name} report does not cover the same files as "
                f"{reference_filter}: {', '.join(details)}"
            )

    tree = {}
    for file_path in sorted(reference_paths):
        group_path = tuple(
            group
            for filter_name in filter_order
            for group in report_groups[filter_name][file_path]
        )
        current = tree
        for group in group_path[:-1]:
            current = current.setdefault(group, {})
        current.setdefault(group_path[-1], []).append(file_path)

    return {"filter_order": filter_order, "tree": tree}


def write_plan(plan, output_path):
    output_path = Path(output_path)
    if output_path.exists():
        print(f"Warning: {output_path} already exists and will be overwritten.", file=sys.stderr)
    if output_path.parent != Path("."):
        output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(plan, file, indent=2, ensure_ascii=False)


def run(config_path, output_path):
    filter_order, report_paths = load_config(config_path)
    reports = {}
    for filter_name, report_path in report_paths.items():
        with report_path.open(encoding="utf-8") as file:
            reports[filter_name] = json.load(file)
    plan = build_plan(filter_order, reports)
    write_plan(plan, output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Build a prioritized JSON file-tree plan from filter reports."
    )
    parser.add_argument("config", help="YAML configuration containing filter order and report paths")
    parser.add_argument(
        "-o", "--output",
        default="media_plan.json",
        help="Path to the output JSON plan (default: media_plan.json)",
    )
    args = parser.parse_args()

    try:
        run(args.config, args.output)
    except (OSError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
