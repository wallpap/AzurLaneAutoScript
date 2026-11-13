# Deploy

This directory holds the Alas installer.

Install the source environment with `uv sync --locked --no-dev` in the Alas root folder.
Run the web interface with `uv run python gui.py`, or the installer with
`uv run python -m deploy.installer`. The default dependency update uses `uv.lock`;
custom `RequirementsFile` settings retain the platform-specific pip installer.

Python 3.8 is pinned in `.python-version` for compatibility with the existing OCR
engine. `pyproject.toml` is the dependency source; `uv.lock` records the resolved
versions for Windows and Linux x86-64. Regenerate the compatibility requirements
with `uv run python -m dev_tools.requirements_updater` after changing dependencies.



# Launcher

Build the Windows desktop and native launcher with `npm run package:win` from
`webapp`. This compiles Electron and `deploy/launcher/Alas.cs`, creates `Alas.exe`
in the source root, and writes a desktop ZIP to `webapp/dist`.

Extract the ZIP into an Alas source checkout and double-click the root `Alas.exe`.
The launcher locates the desktop runtime without depending on the shortcut's
working directory. If no Python environment exists, it installs the locked
dependencies using uv (which must already be installed). The ZIP contains the
desktop runtime, not the complete source or Python environment.

`deploy/launcher/Alas.bat` remains available to run the installer before opening
the desktop. The native launcher opens the desktop directly.

