"""Plumbing shared by every filter: file discovery, EXIF reading, report writing.

Kept free of filter-specific meaning: modules here know that EXIF exists, not
what a capture date or a GPS fix is.
"""
