# Filter_scripts

Scripts for filtering/organizing photos before they get sorted into the final library.

## group_photos_by_date.py

Recursively scans a folder tree for photos and groups them by date.

Files are grouped under `capture_time` when their real EXIF `DateTimeOriginal`
is readable. Everything else (no EXIF tag, or a format exifread can't parse at
all, e.g. PNG, HEIC) falls back to `last_modified`, grouped by file mtime instead.

### Requirements

Create a virtual environment and install dependencies from `requirements.txt`:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Usage

```
python group_photos_by_date.py <root> [-o OUTPUT]
```

- `root` — folder to scan recursively for photos.
- `-o`, `--output` — path to the output JSON report (default: `photos_by_date.json`). A warning is printed if this file already exists, since it will be overwritten.

### Output format

```json
{
  "capture_time": {
    "2024-06-01": ["path/to/photo1.jpg", "path/to/photo2.jpg"],
    "2024-06-02": ["path/to/photo3.jpg"]
  },
  "last_modified": {
    "2024-06-03": ["path/to/unknown.jpg", "path/to/photo.heic"]
  }
}
```

- `capture_time` — capture date (`YYYY-MM-DD`) → sorted list of file paths, from EXIF `DateTimeOriginal`.
- `last_modified` — mtime date (`YYYY-MM-DD`) → list of file paths ordered by mtime within each day, for files with no readable EXIF date or an unsupported format.

### Supported extensions

Scanned: `.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`, `.png`, `.gif`, `.bmp`, `.webp`, `.heic`, `.heif`

EXIF-capable (used for `capture_time`): `.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`. Everything else scanned falls back to `last_modified`.

### Building a Windows executable

Install the build tool in addition to `requirements.txt`:

```
pip install -r requirements-dev.txt
```

Build a single-file `.exe`:

```
pyinstaller --onefile group_photos_by_date.py
```

The executable is written to `dist/group_photos_by_date.exe`. The `build/` folder
and the generated `.spec` file are build artifacts and are gitignored; delete
them freely and rerun the command above to rebuild.

PyInstaller doesn't cross-compile: the `.exe` only runs on the same OS/architecture
it was built on. This build was produced on 64-bit Windows 11, so the resulting
`.exe` only runs on 64-bit Windows.
