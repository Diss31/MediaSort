"""Writing a filter's JSON report."""

import json
import os
import sys


def validate_report(report, expected_filter=None):
    """Checks the common filter report envelope and its recursive group tree."""
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    if set(report) != {"filter", "groups"}:
        raise ValueError("report must contain exactly 'filter' and 'groups'")

    filter_name = report["filter"]
    if not isinstance(filter_name, str) or not filter_name:
        raise ValueError("'filter' must be a non-empty string")
    if expected_filter is not None and filter_name != expected_filter:
        raise ValueError(
            f"expected a {expected_filter!r} report, got {filter_name!r}"
        )

    groups = report["groups"]
    if not isinstance(groups, dict):
        raise ValueError("'groups' must be an object")

    seen_paths = set()

    def validate_group(node, location):
        if isinstance(node, dict):
            for name, child in node.items():
                if not isinstance(name, str) or not name:
                    raise ValueError(f"group names at {location} must be non-empty strings")
                validate_group(child, f"{location}.{name}")
        elif isinstance(node, list):
            for path in node:
                if not isinstance(path, str) or not path:
                    raise ValueError(f"file paths at {location} must be non-empty strings")
                if path in seen_paths:
                    raise ValueError(f"file path {path!r} appears more than once in the report")
                seen_paths.add(path)
        else:
            raise ValueError(f"group {location} must be an object or a list of file paths")

    validate_group(groups, "groups")
    return report


def write_report(report, output_path):
    """Writes report as indented UTF-8 JSON, warning on stderr if it overwrites a file."""
    validate_report(report)
    if os.path.exists(output_path):
        print(f"Warning: {output_path} already exists and will be overwritten.", file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
