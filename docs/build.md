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

Both tracks ship **every** filter; they differ in packaging form and in how the
filters are grouped:

| | Windows executable | Container images |
| --- | --- | --- |
| Artifact | **one** standalone `.exe` running every filter | one image per filter |
| | `mediasort.exe` | `mediasort-date`, `mediasort-geo` |
| Purpose | the actual personal tool, run on a Windows desktop | running the same filters on Kubernetes, one pod per filter |
| Built by | [exec_build.yml](../.github/workflows/exec_build.yml) on `windows-2025` | [image_build.yml](../.github/workflows/image_build.yml) on Linux |
| Installs | `uv sync --extra exe` | `uv sync --extra <filter>` |
| Includes PyInstaller | yes | **never** |

The split differs on purpose: on a desktop, one tool that always produces every
report is simplest to use, while on Kubernetes each filter staying its own image
is what allows one pod per filter.

Adding a filter therefore means adding an extra, a thin Dockerfile, a
per-filter console script for its image, and one entry in the combined CLI
([cli.py](../src/mediasort/cli.py)); nothing about the structure changes.

Which part of [pyproject.toml](../pyproject.toml) feeds which track:

| Section | Goes to |
| --- | --- |
| `dependencies` | both tracks; in containers it is the shared **base image** layer |
| `optional-dependencies.date` / `.geo` | both tracks; in containers, the thin per-filter layer |
| `optional-dependencies.exe` | the executable track only |

**Invariant: PyInstaller never enters a container image.** It is a packaging tool
for the executable channel, useless at runtime, and the `exe` extra exists to keep
it out. [image_build.yml](../.github/workflows/image_build.yml) asserts this on
every published filter image rather than trusting it.

The extra is deliberately named for the distribution *channel* and not for an
operating system: PyInstaller also runs in the Linux devcontainer to produce the
smoke-test binary, so `windows` would be inaccurate. When linters and tests
arrive they belong in a separate `dev` extra, so that the executable build never
installs them and a lint job never installs PyInstaller.

## Windows executable

A single executable, `mediasort.exe`, that runs every filter on a folder, one
after the other, and always writes every report. There is deliberately no way to
run only one filter from it:

```
mediasort.exe <folder> [-o <output folder>] [-t <metres>]
```

- `-o`: folder the reports go to (default: the current folder, created if
  missing), as `photos_by_date.json` and `photos_by_location.json`.
- `-t`: the geo filter's distance threshold, defaulting to the geo filter's own.
- If one filter fails, the others still run; the error is reported on stderr and
  the process exits non-zero.

It is built from [cli.py](../src/mediasort/cli.py), which calls each filter's
functions directly rather than its `main()`, since every filter `main()` parses
its own command line.

PyInstaller analyses a *script* and ignores `[project.scripts]`, so it is pointed
at a two-line shim in [entrypoints/](../entrypoints) that imports the real entry
point from the installed package:

```
uv sync --extra exe
uv run pyinstaller --onefile --name mediasort entrypoints/mediasort_entry.py
```

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

The same rule applies inside each filter image, which installs in two steps
around the `COPY src/`:

| Layer | Contents | Rebuilt when |
|---|---|---|
| base | shared dependencies | `pyproject.toml` / `uv.lock` change |
| child `RUN uv sync --extra <filter> --no-install-project` | that filter's extra dependencies | `pyproject.toml` / `uv.lock` change |
| child `COPY src/` + `RUN uv sync --extra <filter>` | `mediasort` itself | any source change |

Installing the extra *before* copying the source is what keeps a filter's heavy
dependencies cached across code edits. Reversing the order would reinstall them
on every edit — including edits to `mediasort.common`, which touch every image at
once.

That split is also why `uv` is used rather than pip: `uv sync --no-install-project`
installs the resolved dependencies *without* building the project, which plain
`pip install .` cannot express. A second reason is the lockfile — `uv.lock` is
cross-platform, so the pods and the `.exe` resolve to identical dependency
versions. That matters as soon as a third executable consumes the JSON output of
both filters: two filters quietly running different `exifread` versions would
produce reports that disagree.

Known characteristic: the per-filter images `COPY src/` wholesale, so editing one
filter rebuilds the *thin* layer of every image — roughly 8 MB of layer churn per
unrelated edit. The expensive dependency layers still stay cached.

Copying only one filter's folder instead does work, but needs the package
skeleton and `common/` copied too (`mediasort/__init__.py`, `filters/__init__.py`,
`mediasort/common/`), and leaves
each image shipping a broken console script for every *other* filter, because
`[project.scripts]` declares them all and installing generates them all. Fixing
that properly means per-filter package metadata — a separate distribution per
filter — which is more machinery than two filters justify. Revisit if push times
start to hurt, or if a filter gains large assets such as model weights.

### CI and the registry

[image_build.yml](../.github/workflows/image_build.yml) publishes to the GitHub
Container Registry (`ghcr.io/diss31/mediasort-{base,date,geo}`) in three jobs:

| Job | Does | Permission |
| --- | --- | --- |
| `build` | builds and pushes all three images tagged `sha-<commit>`; the filter images are built `FROM` the base pushed for that same commit (`BASE_IMAGE` build arg) | `packages: write` |
| `test` | on a fresh runner, pulls each filter image, runs it against [tests/samples/](../tests/samples) and checks a report was written, then asserts PyInstaller is absent | `packages: read` |
| `promote` | once every filter passes, re-tags the tested digests as `latest`, without rebuilding | `packages: write` |

`test` is end-to-end on purpose: it exercises the published images exactly as a
consumer pulls them, not the build internals. The base is not tested on its own;
it is contained in every filter image that is.

`latest` therefore only ever points at images that passed, and always moves for
all filters together. A failing commit still leaves its `sha-` images in the
registry; [ghcr_cleanup.yml](../.github/workflows/ghcr_cleanup.yml) runs weekly
and keeps the five most recent versions of each package, plus the one tagged
`latest` whatever its age. If `latest` cannot be resolved, it deletes nothing.

Authentication uses the run's automatic `GITHUB_TOKEN`, whose rights are the
job's `permissions:` block — no secret to create. New packages start
**private**; their visibility, and the repository's *Admin* access needed by the
cleanup workflow, are set from each package's settings page.

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
