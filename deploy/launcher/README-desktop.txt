Alas Windows desktop package (x64)

Extract this ZIP into an AzurLaneAutoScript source checkout, keeping the
webapp/dist/win-unpacked directory intact. Double-click Alas.exe in the
project root. Shortcuts may use any working directory.

The source checkout and a Python environment are required. If neither
.venv nor toolkit Python exists, install uv first; Alas.exe then runs
uv sync --locked --no-dev --inexact automatically. The initial installation
requires internet access. Existing configuration files are preserved.

Rebuild from source: cd webapp, then npm run package:win.
This ZIP contains the desktop runtime and launcher, not the game assets,
Python environment, or complete Alas source tree.
