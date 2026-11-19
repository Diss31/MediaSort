"""PyInstaller entry point for the combined executable.

PyInstaller analyses a script file and does not read `[project.scripts]`, so it
needs a real file to trace imports from. Keep this shim trivial: the logic
belongs in the package.
"""

from mediasort.cli import main

main()
