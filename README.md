# MediaSort

Personal tool for organizing a photo/media library.

This is a pedagogical project: design and structure decisions are made deliberately
by the repo owner rather than picked automatically (see
[.github/copilot-instructions.md](.github/copilot-instructions.md)).

## Structure

- [Filter_scripts/](Filter_scripts/) — scripts that filter/organize photos ahead of
  sorting into the final library. See its own README for details on each script.

## Setup

```
python -m venv .venv
.venv\Scripts\activate
```

Each subfolder lists its own dependencies in a `requirements.txt`.
