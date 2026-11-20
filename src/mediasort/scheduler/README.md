# Scheduler

The scheduler reads one report from each configured filter, checks that the
reports use the shared filter-report envelope, and writes a JSON file-tree plan.
It does not copy, move, or modify image files.

## Requirements

The YAML parser is the `scheduler` extra declared in the root
[`pyproject.toml`](../../../pyproject.toml); it is not part of the shared
dependencies. From the repository root:

```sh
uv sync --extra scheduler
```

## Configuration

The YAML config, sampled in [`config.yaml`](../../../config.yaml), has two fields:

- `filter_order` — filters from highest to lowest priority.
- `reports_location` — each filter's report path.

Report paths are resolved relative to the YAML file. Each configured report must
cover the same image paths. Date is prioritized over geo in the sample, so the
result groups by date first, then by location. Date files without capture dates
and geo files without GPS coordinates are placed under `unknown` at their
respective levels.

## Usage

```sh
uv run mediasort-scheduler config.yaml [-o OUTPUT]
```

The default output is `media_plan.json`. The plan JSON has a `filter_order`
array and a nested `tree` object; arrays at the leaves contain image paths.
