# Build and packaging

How MediaSort is structured, and why. For day-to-day usage see the
[root README](../README.md); for what each filter does, see its own README.

## Dependency layout

All dependencies are declared in the root [pyproject.toml](../pyproject.toml)
and pinned in the committed `uv.lock`. Extras split them per consumer:
`[project.dependencies]` is the shared set (the container base image), each
`[project.optional-dependencies]` entry is a per-filter delta, `scheduler`
holds the scheduler's own dependency (the YAML parser, which the filters never
import), and `exe` is the packaging channel.

A `requirements.txt` per filter was rejected because it cannot express "this
dependency is shared" — the base image's list would end up duplicated in a
Dockerfile. A shared `requirements/common.txt` can, but gives no *import*
mechanism for shared code, forcing `PYTHONPATH` juggling; an installed package
needs neither.

The `date` and `geo` extras are empty today (both filters only need `exifread`)
but stay declared so nothing changes shape when a filter grows its own
dependency.

### Package layout

The project uses a
[src-layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/):
`import mediasort` resolves only from an *installed* package. With a flat
layout, an import can silently succeed against the source tree even when the
package was never installed (or a stale copy was), so a filter can pass locally
and be broken inside a pod. Under `src/`, every environment is forced through
the same install the container uses, at the cost of one `uv sync`.

## The two build tracks

Both tracks ship **every** filter; they differ in packaging form and grouping:

| | Windows executable | Container images |
| --- | --- | --- |
| Artifact | **one** standalone `mediasort.exe` running every filter | one image per filter: `mediasort-date`, `mediasort-geo`, plus `mediasort-scheduler` |
| Purpose | the actual personal tool, on a Windows desktop | the same filters on Kubernetes, one pod per filter |
| Built by | [exec_build.yml](../.github/workflows/exec_build.yml) on `windows-2025` | [image_build.yml](../.github/workflows/image_build.yml) on Linux |
| Installs | `uv sync --extra exe` | `uv sync --extra <filter>` |
| Includes PyInstaller | yes | **never** |

The split is deliberate: on a desktop, one tool that always produces every
report is simplest; on Kubernetes, one image per filter is what allows one pod
per filter.

Adding a filter means adding an extra, a thin Dockerfile, a per-filter console
script, and one entry in the combined CLI
([cli.py](../src/mediasort/cli.py)); the structure does not change.

| `pyproject.toml` section | Goes to |
| --- | --- |
| `dependencies` | both tracks; in containers, the shared **base image** layer |
| `optional-dependencies.date` / `.geo` | both tracks; in containers, the thin per-filter layer |
| `optional-dependencies.scheduler` | the scheduler only; the filter images and the executable never install it, the scheduler image does |
| `optional-dependencies.exe` | the executable track only |

**Invariant: PyInstaller never enters a container image.** It is a packaging
tool for the executable channel, and
[image_build.yml](../.github/workflows/image_build.yml) asserts its absence on
every published image rather than trusting the extras split.

The extra is named for the distribution *channel*, not an OS: PyInstaller also
runs in the Linux devcontainer for a smoke-test binary, so `windows` would be
inaccurate. Future linters/tests belong in a separate `dev` extra, so the
executable build never installs them and a lint job never installs PyInstaller.

## Windows executable

One executable running every filter, with deliberately no way to run only one:

```
mediasort.exe <folder> [-o <output folder>] [-t <metres>]
```

- `-o`: report folder (default: current folder), `photos_by_date.json` and
  `photos_by_location.json`.
- `-t`: geo distance threshold, defaulting to the geo filter's own.
- If one filter fails, the others still run; the error goes to stderr and the
  exit code is non-zero.

It is built from [cli.py](../src/mediasort/cli.py), which calls each filter's
functions directly (each filter `main()` parses its own command line).
PyInstaller analyses a *script* and ignores `[project.scripts]`, so it is
pointed at a two-line shim in [entrypoints/](../entrypoints):

```
uv sync --extra exe
uv run pyinstaller --onefile --name mediasort entrypoints/mediasort_entry.py
```

The project must be installed before PyInstaller runs — enforced by the
src-layout. PyInstaller does not cross-compile, hence the Windows runner as the
trusted build.

### Rolling release

The `.exe` is published as a GitHub **release**, not a workflow artifact:
artifacts expire and require a login to download, while a release gives one
permanent, anonymously clickable URL.

The strategy is a single rolling pre-release: every push to `main` force-moves
the `nightly` tag to the built commit and swaps the attached `mediasort.exe`
(`gh release upload --clobber`). `--prerelease` keeps it off the repo's
"Latest release" badge. Chosen over tag-driven releases for zero release
ceremony; the accepted cost is no binary history — only the newest build
exists. The preinstalled `gh` CLI is used instead of a third-party release
action, so nothing new to pin or to trust with the job's `contents: write`
token.

## Container images

One shared base image, one thin image per filter, and one for the scheduler:

```
docker build -f docker/base.Dockerfile -t mediasort-base:latest .
docker build -f docker/date.Dockerfile -t mediasort-date:latest .
docker build -f docker/geo.Dockerfile  -t mediasort-geo:latest  .
docker build -f docker/scheduler.Dockerfile -t mediasort-scheduler:latest .
```

The base holds the shared dependencies and **no project code**, so editing a
filter leaves the dependency layers cached and only the cheap top layer
rebuilds. Negligible with `exifread` alone — decisive once a filter pulls in
something the size of OpenCV. The same rule shapes each filter image:

| Layer | Contents | Rebuilt when |
|---|---|---|
| base | shared dependencies | `pyproject.toml` / `uv.lock` change |
| child `RUN uv sync --extra <filter> --no-install-project` | the filter's extra dependencies | `pyproject.toml` / `uv.lock` change |
| child `COPY src/` + `RUN uv sync --extra <filter>` | `mediasort` itself | any source change |

Installing the extra *before* copying the source keeps a filter's heavy
dependencies cached across code edits. That split is also why `uv` rather than
pip: `--no-install-project` installs resolved dependencies *without* building
the project, which `pip install .` cannot express. Second reason: `uv.lock` is
cross-platform, so pods and the `.exe` resolve identical dependency versions —
reports from two filters must not disagree because of diverging `exifread`
versions.

Known characteristic: filter images `COPY src/` wholesale, so one edit rebuilds
the thin layer of every image (~8 MB churn each). Copying per-filter folders
instead needs the package skeleton and `common/` copied too, and still ships
every other filter's (broken) console script; fixing that properly means one
distribution per filter — more machinery than two filters justify. Revisit if
push times hurt or a filter gains large assets.

### CI and the registry

[image_build.yml](../.github/workflows/image_build.yml) publishes to
`ghcr.io/diss31/mediasort-{base,date,geo,scheduler}` in five jobs:

| Job | Does | Permission |
| --- | --- | --- |
| `build` | builds and pushes all four images tagged `sha-<commit>`; filter and scheduler images are built `FROM` the base pushed for that same commit (`BASE_IMAGE` arg) | `packages: write` |
| `test` | on a fresh runner, pulls each filter image, runs it against [tests/samples/](../tests/samples), checks a report was written, asserts PyInstaller is absent | `packages: read` |
| `test-scheduler` | runs the date and geo images to produce reports, then runs the scheduler image on them with a YAML config, checks a plan was written, asserts PyInstaller is absent | `packages: read` |
| `promote` | once every image passes, re-tags the tested digests as `latest`, without rebuilding | `packages: write` |
| `cleanup` | calls [ghcr_cleanup.yml](../.github/workflows/ghcr_cleanup.yml) with the four package names | `packages: write` |

`test` is end-to-end on purpose: it exercises the published images exactly as a
consumer pulls them. The base is not tested alone; it is contained in every
image that is. `latest` only ever points at images that passed, and
moves for all images together.

The base is pushed rather than kept local to the runner by choice, not
necessity: `FROM` a registry reference pinned to the exact commit means a
filter image can never pick up a stale base (and survives the build ever
splitting across runners), and the base behind any published image stays
pullable for debugging.

Cleanup runs as the final job of the same run (`needs: promote`), keeping the
five most recent versions of each package. Running only right after a
successful promotion is what makes that safe: `latest` has just moved, so it is
always among the five newest and needs no explicit digest exclusion (an earlier
scheduled variant had to resolve and exclude it). `ghcr_cleanup.yml` is a
reusable `workflow_call` workflow; with a single caller today that is
deliberate over-engineering kept for learning, paying off only once several
workflows produce images.

Authentication uses the run's automatic `GITHUB_TOKEN`, scoped by each job's
`permissions:` block — no secret to create. New packages start **private**;
their visibility, and the repository's *Admin* access the cleanup needs, are
set from each package's settings page.

## Devcontainer

[.devcontainer/devcontainer.json](../.devcontainer/devcontainer.json) provides
an easy-to-rebuild Linux dev environment (Debian + Python 3.12) instead of
requiring a local Windows install. It diverges from the shipped product on
purpose: PyInstaller inside it produces a Linux ELF, only validating that the
packaging step works; the `windows-2025` build in
[exec_build.yml](../.github/workflows/exec_build.yml) remains the trusted one.
