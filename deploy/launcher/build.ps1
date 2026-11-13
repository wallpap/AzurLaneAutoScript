$ErrorActionPreference = 'Stop'
$launcherDirectory = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$projectRoot = (Resolve-Path (Join-Path $launcherDirectory '../..')).Path
$webapp = Join-Path $projectRoot 'webapp'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET/Framework64/v4.0.30319/csc.exe'

if (!(Test-Path -LiteralPath $compiler)) {
    throw 'The .NET Framework 4 C# compiler is required to build Alas.exe.'
}

Push-Location $projectRoot
try {
    & uv sync --locked --no-dev --inexact
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
} finally {
    Pop-Location
}

Push-Location $webapp
$previousVersion = $env:VITE_APP_VERSION
try {
    $version = & node -p "require('./electron-builder.config.js').extraMetadata.version"
    if ($LASTEXITCODE -ne 0) { throw 'Cannot determine the desktop version.' }
    $env:VITE_APP_VERSION = $version
    if (!(Test-Path -LiteralPath 'node_modules/electron-builder')) {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Desktop dependency installation failed.' }
    }
    & npm.cmd run compile
    if ($LASTEXITCODE -ne 0) { throw 'Desktop compilation failed.' }

    $source = Join-Path $launcherDirectory 'Alas.cs'
    $icon = Join-Path $launcherDirectory 'icon.ico'
    $launcher = Join-Path $projectRoot 'Alas.exe'
    & $compiler /nologo /target:winexe /optimize+ /reference:System.Windows.Forms.dll "/win32icon:$icon" "/out:$launcher" $source
    if ($LASTEXITCODE -ne 0) { throw 'Launcher compilation failed.' }

    $staging = Join-Path $webapp "dist/desktop-$version-$([guid]::NewGuid().ToString('N'))"
    $runtime = Join-Path $staging 'webapp/dist/win-unpacked'
    New-Item -ItemType Directory -Path $runtime -Force | Out-Null
    Copy-Item -Path 'dist/win-unpacked/*' -Destination $runtime -Recurse
    Copy-Item -LiteralPath "$projectRoot/Alas.exe" -Destination $staging
    Copy-Item -LiteralPath (Join-Path $launcherDirectory 'README-desktop.txt') -Destination $staging
    $archive = Join-Path $webapp "dist/Alas-desktop-$version-win-x64.zip"
    Compress-Archive -Path "$staging/*" -DestinationPath $archive -Force
    $resolvedStaging = (Resolve-Path -LiteralPath $staging).Path
    $distRoot = (Resolve-Path -LiteralPath (Join-Path $webapp 'dist')).Path + [IO.Path]::DirectorySeparatorChar
    if (!$resolvedStaging.StartsWith($distRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Package staging folder is outside the desktop output folder.'
    }
    Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
    Write-Output "Launcher: $projectRoot/Alas.exe"
    Write-Output "Desktop package: $archive"
} finally {
    $env:VITE_APP_VERSION = $previousVersion
    Pop-Location
}
