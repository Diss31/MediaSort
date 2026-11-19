"""PyInstaller entry point for the date filter.

PyInstaller analyses a script file and does not read `[project.scripts]`, so it
needs a real file to trace imports from. Keep this shim trivial: the logic
belongs in the package, which is what the container images import directly.
"""

from mediasort.filters.date import main

main()
