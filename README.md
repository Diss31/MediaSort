# MediaSort

Personal tool for organizing a photo/media library.

This is a pedagogical project: design and structure decisions are made deliberately
by the repo owner rather than picked automatically (see
[.github/copilot-instructions.md](.github/copilot-instructions.md)).

## Structure

Filters that process photos ahead of sorting them into the final library. Every
filter ships both as a standalone executable and as a container image, and keeps
its own README next to its code:

- [src/mediasort/filters/date/](src/mediasort/filters/date/README.md) — groups photos by date.
- [src/mediasort/filters/geo/](src/mediasort/filters/geo/README.md) — groups photos by GPS location.

Plumbing shared by every filter — image discovery, raw EXIF reading, JSON report
writing — lives in [src/mediasort/common/](src/mediasort/common). It deliberately
holds no filter-specific meaning: parsing a capture date or a GPS fix stays in
the filter that owns it.

## Setup

Dependencies for every filter are declared centrally in [pyproject.toml](pyproject.toml)
and pinned in the committed `uv.lock`. [uv](https://docs.astral.sh/uv/) is the only
dependency tool used here:

```
uv sync
```

Then run a filter:

```
uv run mediasort-date <folder>
uv run mediasort-geo  <folder>
```

A [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) is provided for an
easy-to-rebuild Linux dev environment (Debian + Python 3.12), instead of requiring a
local Windows install.

## Building

Standalone executables:

```
uv sync --extra exe
uv run pyinstaller --onefile --name group_photos_by_date entrypoints/date_entry.py
```

Container images:

```
docker build -f docker/base.Dockerfile -t mediasort-base:latest .
docker build -f docker/date.Dockerfile -t mediasort-date:latest .
```

See [docs/build.md](docs/build.md) for the full build and packaging setup: how the
two tracks relate, how dependencies are split between the shared base image and
each filter, and why it is arranged that way.
