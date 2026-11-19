# Build and packaging

How MediaSort is structured, and why. For day-to-day usage see the
[root README](../README.md); for what each filter does, see its own README.

## Dependency layout

All dependencies are declared in a single root [pyproject.toml](../pyproject.toml)
and pinned in the committed `uv.lock`. There is no `requirements.txt` per filter.

### Why one file instead of one `requirements.txt` per filter

Splitting dependencies per filter and centralising them are not actually in
conflict, because they are separate questions: *where the list is declared* versus
*what gets installed into each pod*. Extras answer both at once —
`[project.dependencies]` is the shared set that goes into the base image, and each
`[project.optional-dependencies]` entry is the per-filter delta added in a thin
layer on top. One source of truth, still minimal images.

The alternative — a `requirements.txt` per filter — cannot express "this
dependency is shared", so the base image's package list would have to be
hardcoded in a Dockerfile, which is exactly the duplication worth avoiding. A
shared `requirements/common.txt` does express it, but gives no *import*
mechanism: the moment shared code appears, it needs `PYTHONPATH` juggling or
copying a folder into every build context. An installed package needs neither.

The `date` and `geo` extras are empty today because both filters only need
`exifread`. They stay declared so that nothing about the build commands or the
Dockerfiles has to change shape the first time a filter grows its own dependency.

### Package layout

The project uses a
[src-layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/):
`import mediasort` resolves only from an *installed* package, never from the
source tree sitting in the working directory.

This matters because the repository root is on `sys.path` when Python runs from
there. With a flat layout, an import can silently succeed against the source tree
even when the package was never installed, or a stale copy was — so a filter can
pass locally and be broken inside a pod. Under `src/`, every environment is forced
through the same install the container uses. The cost is one `uv sync` before
anything runs.

## The two build tracks

Both tracks ship **every** filter; they differ only in packaging form, not in
capability:

| | Windows executables | Container images |
| --- | --- | --- |
| Artifact | one standalone `.exe` per filter | one image per filter |
| | `group_photos_by_date.exe`, `group_photos_by_location.exe` | `mediasort-date`, `mediasort-geo` |
| Purpose | the actual personal tool, run on a Windows desktop | running the same filters on Kubernetes |
| Built by | [exec_build.yml](../.github/workflows/exec_build.yml) on `windows-2025` | [image_build.yml](../.github/workflows/image_build.yml) on Linux |
| Installs | `uv sync --extra exe` | `uv sync --extra <filter>` |
| Includes PyInstaller | yes | **never** |

Anything that becomes a filter or a standalone utility — including the planned
tool that merges the filters' JSON outputs — is expected to gain both an
executable and an image. Adding one means adding an extra, an entry point, a
shim, and a thin Dockerfile; nothing about the structure changes.

> **Known gap:** [exec_build.yml](../.github/workflows/exec_build.yml) currently
> builds only the date executable. That is unfinished CI, not a design boundary —
> every filter is buildable as an executable today, and the geo command below
> works locally right now.

Which part of [pyproject.toml](../pyproject.toml) feeds which track:

| Section | Goes to |
| --- | --- |
| `dependencies` | both tracks; in containers it is the shared **base image** layer |
| `optional-dependencies.date` / `.geo` | both tracks; in containers, the thin per-filter layer |
| `optional-dependencies.exe` | the executable track only |

**Invariant: PyInstaller never enters a container image.** It is a packaging tool
for the executable channel, useless at runtime, and the `exe` extra exists to keep
it out. [image_build.yml](../.github/workflows/image_build.yml) asserts this on
every build rather than trusting it.

The extra is deliberately named for the distribution *channel* and not for an
operating system: PyInstaller also runs in the Linux devcontainer to produce the
smoke-test binary, so `windows` would be inaccurate. When linters and tests
arrive they belong in a separate `dev` extra, so that the executable build never
installs them and a lint job never installs PyInstaller.

## Windows executables

One executable per filter. PyInstaller analyses a *script* and ignores
`[project.scripts]`, so it is pointed at a two-line shim in
[entrypoints/](../entrypoints) that imports the real entry point from the
installed package:

```
uv sync --extra exe
uv run pyinstaller --onefile --name group_photos_by_date     entrypoints/date_entry.py
uv run pyinstaller --onefile --name group_photos_by_location entrypoints/geo_entry.py
```

`--name` keeps each artifact's filename independent of its shim's filename.

The project must be installed before PyInstaller runs, or `mediasort` is not
importable — with src-layout this is enforced rather than merely recommended.

PyInstaller does not cross-compile: the `.exe` only runs on the OS/architecture it
was built on, which is why the trusted build happens on a Windows runner.

## Container images

One shared base image plus one thin image per filter:

```
docker build -f docker/base.Dockerfile -t mediasort-base:latest .
docker build -f docker/date.Dockerfile -t mediasort-date:latest .
docker build -f docker/geo.Dockerfile  -t mediasort-geo:latest  .
```

The base holds the shared dependencies and **no project code**. A Docker image is
a stack of layers, and a rebuild reuses cached layers until the first changed
input; keeping the source out of the base means editing a filter leaves the
dependency layer a cache hit and only the cheap top layer rebuilds, instead of
reinstalling every dependency on each source change. Negligible with `exifread`
alone — decisive once a filter pulls in something the size of OpenCV.

That split is also why `uv` is used rather than pip: `uv sync --no-install-project`
installs the resolved dependencies *without* building the project, which plain
`pip install .` cannot express. A second reason is the lockfile — `uv.lock` is
cross-platform, so the pods and the `.exe` resolve to identical dependency
versions. That matters as soon as a third executable consumes the JSON output of
both filters: two filters quietly running different `exifread` versions would
produce reports that disagree.

Known characteristic: the per-filter images `COPY src/` wholesale, so editing one
filter rebuilds the *thin* layer of every image — roughly 8 MB of layer churn per
unrelated edit. The expensive dependency layer still stays cached.

Copying only one filter's folder instead does work, but needs the package
skeleton copied too (`mediasort/__init__.py`, `filters/__init__.py`), and leaves
each image shipping a broken console script for every *other* filter, because
`[project.scripts]` declares them all and installing generates them all. Fixing
that properly means per-filter package metadata — a separate distribution per
filter — which is more machinery than two filters justify. Revisit if push times
start to hurt, or if a filter gains large assets such as model weights.

CI builds these images to prove the Dockerfiles still work, runs each one against
[tests/samples/](../tests/samples), and discards them. Nothing is pushed to a
registry yet.

## Devcontainer

A [.devcontainer/devcontainer.json](../.devcontainer/devcontainer.json) provides an
easy-to-rebuild Linux dev environment (Debian + Python 3.12), instead of requiring
a local Windows install.

It is a local convenience only, and diverges from the final expected result:
`pyinstaller` run inside the devcontainer produces a Linux ELF binary, not the
Windows `.exe` the project targets — it only validates that the PyInstaller
packaging step itself works. The
[exec_build.yml](../.github/workflows/exec_build.yml) GitHub Action builds on
`windows-2025` and is the trusted source for catching any discrepancies between
the Linux devcontainer build and the actual Windows build.
