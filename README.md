# MediaSort

Personal tool for organizing a photo/media library.

This is a pedagogical project: design and structure decisions are made deliberately
by the repo owner rather than picked automatically (see
[.github/copilot-instructions.md](.github/copilot-instructions.md)).

## Structure

Filters that process photos ahead of sorting them into the final library. Every
filter ships as a container image, and all filters ship together as one
standalone executable. Each filter keeps its own README next to its code:

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

Then run every filter at once (writes both reports to the current folder, or
`-o <folder>`):

```
uv run mediasort <folder>
```

or a single filter:

```
uv run mediasort-date <folder>
uv run mediasort-geo  <folder>
```

A [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) is provided for an
easy-to-rebuild Linux dev environment (Debian + Python 3.12), instead of requiring a
local Windows install. The image also bakes in the latest [actionlint](https://github.com/rhysd/actionlint)
release for checking GitHub Actions workflows (`actionlint` from the repository root).
New actionlint releases are picked up automatically on the next **Dev Containers:
Rebuild Container** — the Dockerfile `ADD`s upstream's install script, whose content
changes on each release, which invalidates the cached install layer.

On a network with a TLS-intercepting proxy, HTTPS downloads inside the container fail
certificate verification until the proxy's root CA is trusted. One-time setup: copy the
CA (PEM, `.crt` extension) into `.devcontainer/` — it is gitignored and baked into the
image at build time by [.devcontainer/Dockerfile](.devcontainer/Dockerfile):

```
cp /etc/pki/ca-trust/source/anchors/bluecoat-root.crt .devcontainer/
```

On networks without TLS interception, skip this; the build works with no `.crt` present.
After adding or rotating a cert, use **Dev Containers: Rebuild Container** — "Reopen in
Container" reuses the old image.

## Building

Standalone executable (runs every filter):

```
uv sync --extra exe
uv run pyinstaller --onefile --name mediasort entrypoints/mediasort_entry.py
```

Container images:

```
docker build -f docker/base.Dockerfile -t mediasort-base:latest .
docker build -f docker/date.Dockerfile -t mediasort-date:latest .
```

See [docs/build.md](docs/build.md) for the full build and packaging setup: how the
two tracks relate, how dependencies are split between the shared base image and
each filter, and why it is arranged that way.
