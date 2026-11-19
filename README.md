# MediaSort

Personal tool for organizing a photo/media library.

This is a pedagogical project: design and structure decisions are made deliberately
by the repo owner rather than picked automatically (see
[.github/copilot-instructions.md](.github/copilot-instructions.md)).

## Structure

Scripts that filter/organize photos ahead of sorting into the final library. Each
folder is standalone and has its own README:

- [Filter_scripts/date/](Filter_scripts/date/README.md) — groups photos by date.
- [Filter_scripts/geo/](Filter_scripts/geo/README.md) — groups photos by GPS location.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
```

Each subfolder lists its own dependencies in a `requirements.txt`.

### Devcontainer

A [.devcontainer/devcontainer.json](.devcontainer/devcontainer.json) is provided for an easy-to-rebuild
Linux-based dev environment (Debian + Python 3.12), instead of requiring a local Windows install.

This is a local convenience only, and diverges from the final expected result:
`pyinstaller` run inside the devcontainer produces a Linux ELF binary, not the Windows `.exe`
the project targets — it only validates that the PyInstaller packaging step itself works.
The [.github/workflows/exec_build.yml](.github/workflows/exec_build.yml) GitHub Action builds on
`windows-2025` and is the trusted source for catching any discrepancies between the Linux
devcontainer build and the actual Windows build.
