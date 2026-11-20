"""
Recursively scans a folder tree for photos and groups them by GPS location.

Photos whose EXIF GPS coordinates are readable are clustered by proximity: two
photos within the threshold distance belong to the same cluster, and clustering
chains transitively (A near B, B near C puts all three together). Clusters are
numbered, not reverse-geocoded. Everything with no usable GPS falls into
"no_location" -- unlike capture dates there is no fallback, a photo without GPS
simply has no location.

Dependencies are declared in the root pyproject.toml.
"""

import argparse
import math

from mediasort.common.exif import read_exif_tags
from mediasort.common.files import find_images
from mediasort.common.report import write_report

GPS_LATITUDE_TAG = "GPS GPSLatitude"
GPS_LATITUDE_REF_TAG = "GPS GPSLatitudeRef"
GPS_LONGITUDE_TAG = "GPS GPSLongitude"
GPS_LONGITUDE_REF_TAG = "GPS GPSLongitudeRef"

NEGATIVE_REFS = {"S", "W"}

EARTH_RADIUS_M = 6371008.8
DEFAULT_THRESHOLD_M = 500.0


def dms_to_decimal(tag, ref):
    """Converts an exifread degrees/minutes/seconds tag to signed decimal degrees."""
    try:
        degrees, minutes, seconds = tag.values
    except (AttributeError, TypeError, ValueError):
        return None

    try:
        decimal = (
            degrees.num / degrees.den
            + minutes.num / minutes.den / 60
            + seconds.num / seconds.den / 3600
        )
    except (AttributeError, ZeroDivisionError):
        return None

    return -decimal if str(ref).strip().upper() in NEGATIVE_REFS else decimal


def read_gps(path):
    """Returns (latitude, longitude) in decimal degrees, or None if unavailable."""
    tags = read_exif_tags(path)
    if tags is None:
        return None

    try:
        lat_tag = tags[GPS_LATITUDE_TAG]
        lat_ref = tags[GPS_LATITUDE_REF_TAG]
        lon_tag = tags[GPS_LONGITUDE_TAG]
        lon_ref = tags[GPS_LONGITUDE_REF_TAG]
    except KeyError:
        return None

    lat = dms_to_decimal(lat_tag, lat_ref)
    lon = dms_to_decimal(lon_tag, lon_ref)

    if lat is None or lon is None:
        return None
    if abs(lat) > 90 or abs(lon) > 180:
        return None
    # All-zero coordinates mean a failed GPS fix, not a spot in the Gulf of Guinea.
    if lat == 0 and lon == 0:
        return None

    return lat, lon


def haversine_m(point_a, point_b):
    """Great-circle distance in metres between two (latitude, longitude) pairs."""
    lat1, lon1 = math.radians(point_a[0]), math.radians(point_a[1])
    lat2, lon2 = math.radians(point_b[0]), math.radians(point_b[1])

    a = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


class UnionFind:
    def __init__(self, size):
        self._parent = list(range(size))
        self._size = [1] * size

    def find(self, item):
        root = item
        while self._parent[root] != root:
            root = self._parent[root]
        while self._parent[item] != root:
            self._parent[item], item = root, self._parent[item]
        return root

    def union(self, a, b):
        root_a, root_b = self.find(a), self.find(b)
        if root_a == root_b:
            return
        if self._size[root_a] < self._size[root_b]:
            root_a, root_b = root_b, root_a
        self._parent[root_b] = root_a
        self._size[root_a] += self._size[root_b]


def cluster_by_distance(points, threshold_m):
    """Groups point indices so that any two points within threshold_m end up together."""
    # Pairwise comparison is O(n^2); bucket points into a grid first if it gets slow.
    union_find = UnionFind(len(points))
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            if haversine_m(points[i], points[j]) <= threshold_m:
                union_find.union(i, j)

    clusters = {}
    for index in range(len(points)):
        clusters.setdefault(union_find.find(index), []).append(index)
    return list(clusters.values())


def group_photos(root, threshold_m):
    located_paths = []
    points = []
    no_location = []

    for path in find_images(root):
        coordinates = read_gps(path)

        if coordinates is None:
            no_location.append(path)
        else:
            located_paths.append(path)
            points.append(coordinates)

    clusters = [
        [located_paths[index] for index in indices]
        for indices in cluster_by_distance(points, threshold_m)
    ]
    return clusters, no_location


def build_report(clusters, no_location):
    sorted_clusters = sorted(
        (sorted(paths) for paths in clusters),
        key=lambda paths: (-len(paths), paths[0]),
    )
    return {
        "filter": "geo",
        "groups": {
            "locations": {
                f"location_{number}": paths
                for number, paths in enumerate(sorted_clusters, start=1)
            },
            "no_location": sorted(no_location),
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Group photos by EXIF GPS location into a report file."
    )
    parser.add_argument("root", help="Root folder to scan recursively for photos")
    parser.add_argument(
        "-o", "--output",
        default="photos_by_location.json",
        help="Path to the output JSON report (default: photos_by_location.json)",
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=DEFAULT_THRESHOLD_M,
        help=(
            "Distance in metres below which two photos are considered the same "
            f"location (default: {DEFAULT_THRESHOLD_M:g})"
        ),
    )
    args = parser.parse_args()

    if args.threshold <= 0:
        parser.error("--threshold must be greater than 0")

    clusters, no_location = group_photos(args.root, args.threshold)
    report = build_report(clusters, no_location)
    write_report(report, args.output)
    summarize(clusters, no_location, args.output)


def summarize(clusters, no_location, output_path):
    """Prints the scan counts and where the report was written."""
    located_count = sum(len(paths) for paths in clusters)
    print(
        f"Scanned {located_count + len(no_location)} image(s): "
        f"{located_count} with GPS grouped into {len(clusters)} location(s), "
        f"{len(no_location)} without usable GPS."
    )
    print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
