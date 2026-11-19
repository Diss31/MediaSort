"""Writing a filter's JSON report."""

import json
import os
import sys


def write_report(report, output_path):
    """Writes report as indented UTF-8 JSON, warning on stderr if it overwrites a file."""
    if os.path.exists(output_path):
        print(f"Warning: {output_path} already exists and will be overwritten.", file=sys.stderr)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
