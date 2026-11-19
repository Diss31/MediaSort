# Geo filter

Groups photos by GPS location, ahead of sorting them into the final library.

## mediasort.filters.geo

Recursively scans a folder tree for photos, reads their EXIF GPS coordinates, and
clusters them by proximity.

Clustering is *transitive*: if A is within the threshold of B, and B is within the
threshold of C, all three land in the same cluster — even when A and C are further
apart than the threshold. This follows real movement well, but a dense trail of
photos along a street can chain into one large cluster.

Clusters are numbered (`location_1`, `location_2`, …), not named — there is no
reverse-geocoding, so no network access and no place names.

Unlike the [date filter](../date/README.md) there is **no fallback**: capture dates can fall back
to the file mtime, but a photo without GPS simply has no location and goes to
`no_location`.

### Requirements

Dependencies are declared centrally in the root [`pyproject.toml`](../../../../pyproject.toml),
not per filter. From the repository root:

```
uv sync
```

### Usage

```
uv run mediasort-geo <root> [-o OUTPUT] [-t THRESHOLD]
```

- `root` — folder to scan recursively for photos.
- `-o`, `--output` — path to the output JSON report (default: `photos_by_location.json`). A warning is printed if this file already exists, since it will be overwritten.
- `-t`, `--threshold` — distance in metres below which two photos count as the same location (default: `500`).

### Output format

```json
{
  "locations": {
    "location_1": ["path/to/photo1.jpg", "path/to/photo2.jpg"],
    "location_2": ["path/to/photo3.jpg"]
  },
  "no_location": ["path/to/screenshot.png", "path/to/stripped.jpg"]
}
```

- `locations` — cluster name → sorted list of file paths. Clusters are numbered by photo count, descending (ties broken by first path), so the same input folder always produces the same numbering.
- `no_location` — sorted list of files with no usable GPS.

### Supported extensions

Scanned: `.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`, `.heic`, `.heif`, `.png`, `.gif`, `.bmp`, `.webp`

GPS is only probed on `.jpg`, `.jpeg`, `.jpe`, `.tif`, `.tiff`, `.heic`, `.heif`. EXIF GPS lives in the same metadata block as `DateTimeOriginal`, so the formats that can carry a capture date are the same ones that can carry coordinates:

| Format | EXIF GPS | Notes |
| --- | --- | --- |
| `.jpg` `.jpeg` `.jpe` | yes | The usual carrier for phone GPS. |
| `.tif` `.tiff` | yes | Full EXIF with a GPS IFD. |
| `.heic` `.heif` | best-effort | Default on modern iPhones and they do record GPS, but exifread's HEIC parsing does not succeed on every file. Failures fall into `no_location`. |
| `.png` `.webp` | no | Both can technically hold an EXIF chunk, but exifread does not read it. |
| `.gif` `.bmp` | no | No metadata container at all. |

Note that even a JPEG often has no GPS: location services may have been off, messaging
apps strip EXIF when re-encoding, and screenshots never had coordinates. A large
`no_location` bucket is expected on a real library.

Photos whose GPS tags are present but unusable — malformed values, or an all-zero
`0°, 0°` fix — are treated as having no location rather than being clustered at
"Null Island".

### Building a Windows executable

Install the packaging tool via the `exe` extra, then build a single-file `.exe`
from the entry point shim:

```
uv sync --extra exe
uv run pyinstaller --onefile --name group_photos_by_location entrypoints/geo_entry.py
```

Both commands run from the repository root. PyInstaller analyses a script file
and ignores `[project.scripts]`, which is why it is pointed at the two-line shim
in [`entrypoints/`](../../../../entrypoints) rather than at the package.

The executable is written to `dist/group_photos_by_location.exe`. The `build/` folder
and the generated `.spec` file are build artifacts and are gitignored; delete them
freely and rerun the command above to rebuild.

PyInstaller doesn't cross-compile: the `.exe` only runs on the same OS/architecture
it was built on.
