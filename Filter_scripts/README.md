# Filter_scripts

Scripts for filtering/organizing photos before they get sorted into the final library.

## group_photos_by_date.py

Recursively scans a folder tree for photos and groups them by the date they were
**actually taken** (EXIF `DateTimeOriginal`), not by file mtime/ctime.

Photos without a readable EXIF capture date are listed separately under `no_exif`,
ordered by file mtime (best-effort, since it's all we have).

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
- `-o`, `--output` — path to the output JSON report (default: `photos_by_date.json`).

### Output format

```json
{
  "by_date": {
    "2024-06-01": ["path/to/photo1.jpg", "path/to/photo2.jpg"],
    "2024-06-02": ["path/to/photo3.jpg"]
  },
  "no_exif": [
    { "path": "path/to/unknown.jpg", "mtime": "2024-06-03T10:15:00" }
  ]
}
```

- `by_date` — capture date (`YYYY-MM-DD`) → sorted list of file paths.
- `no_exif` — files with no readable EXIF date, each with its file mtime, sorted oldest first.

### Supported extensions

`.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`, `.png`, `.gif`, `.bmp`, `.webp`, `.heic`, `.heif`
