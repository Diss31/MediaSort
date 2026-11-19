# Date filter

Groups photos by date, ahead of sorting them into the final library.

## mediasort.filters.date

Recursively scans a folder tree for photos and groups them by date.

Files are grouped under `capture_time` when their real EXIF `DateTimeOriginal`
is readable. Everything else (no EXIF tag, a format that can't carry EXIF such as
PNG, or a HEIC/HEIF file exifread fails to parse) falls back to `last_modified`,
grouped by file mtime instead.

### Requirements

Dependencies are declared centrally in the root [`pyproject.toml`](../../../../pyproject.toml),
not per filter. From the repository root:

```
uv sync
```

### Usage

```
uv run mediasort-date <root> [-o OUTPUT]
```

- `root` — folder to scan recursively for photos.
- `-o`, `--output` — path to the output JSON report (default: `photos_by_date.json`). A warning is printed if this file already exists, since it will be overwritten.

### Output format

```json
{
  "capture_time": {
    "2024-06-01": ["path/to/photo1.jpg", "path/to/photo2.jpg"],
    "2024-06-02": ["path/to/photo3.jpg", "path/to/photo4.heic"]
  },
  "last_modified": {
    "2024-06-03": ["path/to/unknown.jpg", "path/to/screenshot.png"]
  }
}
```

- `capture_time` — capture date (`YYYY-MM-DD`) → sorted list of file paths, from EXIF `DateTimeOriginal`.
- `last_modified` — mtime date (`YYYY-MM-DD`) → list of file paths ordered by mtime within each day, for files with no readable EXIF date or an unsupported format.

### Supported extensions

Scanned: `.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`, `.png`, `.gif`, `.bmp`, `.webp`, `.heic`, `.heif`

EXIF-capable (used for `capture_time`): `.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`, and best-effort `.heic`, `.heif` — exifread's HEIC parsing does not succeed on every file, and failures fall back to `last_modified`. Everything else scanned falls back to `last_modified`.

These are the same formats the [geo filter](../geo/README.md) probes for GPS: both
read EXIF through the shared `mediasort.common.exif` reader.

### Building a Windows executable

Install the packaging tool via the `exe` extra, then build a single-file `.exe`
from the entry point shim:

```
uv sync --extra exe
uv run pyinstaller --onefile --name group_photos_by_date entrypoints/date_entry.py
```

Both commands run from the repository root. PyInstaller analyses a script file
and ignores `[project.scripts]`, which is why it is pointed at the two-line shim
in [`entrypoints/`](../../../../entrypoints) rather than at the package.

The executable is written to `dist/group_photos_by_date.exe`. The `build/` folder
and the generated `.spec` file are build artifacts and are gitignored; delete
them freely and rerun the command above to rebuild.

PyInstaller doesn't cross-compile: the `.exe` only runs on the same OS/architecture
it was built on. This build was produced on 64-bit Windows 11, so the resulting
`.exe` only runs on 64-bit Windows.
