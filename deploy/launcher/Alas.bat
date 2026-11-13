@rem
@echo off

set "_root=%~dp0"
set "_root=%_root:~0,-1%"
if not exist "%_root%\pyproject.toml" set "_root=%~dp0..\.."
cd /d "%_root%"
echo "%_root%

color F0

set "_pyBin=%_root%\toolkit"
set "_GitBin=%_root%\toolkit\Git\mingw64\bin"
set "_adbBin=%_root%\toolkit\Lib\site-packages\adbutils\binaries"
set "PATH=%_root%\toolkit\alias;%_root%\toolkit\command;%_pyBin%;%_pyBin%\Scripts;%_GitBin%;%_adbBin%;%PATH%"

title Alas Updater
uv sync --locked --no-dev --inexact
if %errorlevel% neq 0 (
    pause >nul
    exit /b 1
)
uv run --locked --no-sync python -m deploy.installer
if %errorlevel% neq 0 (
    pause >nul
) else (
    if exist "%_root%\webapp\dist\win-unpacked\alas.exe" (
        start "Alas" "%_root%\webapp\dist\win-unpacked\alas.exe"
    ) else (
        start "Alas" "%_root%\toolkit\webapp\alas.exe"
    )
)
