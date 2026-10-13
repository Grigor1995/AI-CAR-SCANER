$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$canonicalBuilder = Join-Path $root 'scripts\build_windows_standalone.ps1'

if (-not (Test-Path $canonicalBuilder)) {
    throw "Canonical build script was not found: $canonicalBuilder"
}

# Keep the legacy entry point, but use one maintained packaging implementation.
& $canonicalBuilder
