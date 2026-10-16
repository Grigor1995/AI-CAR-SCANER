<#
.SYNOPSIS
  Build a clean, reviewable Windows x64 Desktop icon preview.
.DESCRIPTION
  Creates standalone AICarScanner.exe and backend_service.exe using the
  repository's canonical PyInstaller specs. Keeps existing dist/ and
  dist-release/ contents outside the icon-preview subfolder intact.
#>
[CmdletBinding()]
param([switch]$SkipIconTests)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$buildBase = Join-Path $root 'build-release'
$distBase = Join-Path $root 'dist-release'
$work = Join-Path $buildBase 'icon-preview'
$dist = Join-Path $distBase 'icon-preview'
$venv = Join-Path $buildBase 'venv-icon-preview'
$python = Join-Path $venv 'Scripts\python.exe'
$zip = Join-Path $distBase 'AICarScanner-icon-preview.zip'

function Assert-LastExit([string]$step) {
    if ($LASTEXITCODE -ne 0) {
        throw "$step failed with exit code $LASTEXITCODE"
    }
}

Push-Location $root
try {
    New-Item -ItemType Directory -Path $buildBase, $distBase -Force | Out-Null
    if (-not (Test-Path $python)) {
        $systemPython = (Get-Command python -ErrorAction Stop).Source
        & $systemPython -m venv $venv
        Assert-LastExit 'Creating the isolated Python environment'
    }

    & $python -m pip install --upgrade pip setuptools wheel
    Assert-LastExit 'Updating build tools'
    & $python -m pip install -r requirements.txt
    Assert-LastExit 'Installing backend and GUI dependencies'
    & $python -m pip install -r apps\desktop\requirements-dev.txt
    Assert-LastExit 'Installing Desktop test dependencies'

    if (-not $SkipIconTests) {
        & $python -m pytest -q apps/desktop/tests/test_prepare_windows_icon_coverage.py
        Assert-LastExit 'Desktop icon unit tests'
    }

    # The canonical source is assets/AI-Car-Scanner-master.png.
    # prepare_windows_icon.py regenerates PNG, WEBP and ICO from that master.
    & $python apps/desktop/prepare_windows_icon.py
    Assert-LastExit 'Regenerating Desktop icons'

    if (Test-Path $dist) { Remove-Item $dist -Recurse -Force }
    if (Test-Path $work) { Remove-Item $work -Recurse -Force }
    New-Item -ItemType Directory -Path $dist, $work -Force | Out-Null

    & $python -m PyInstaller --noconfirm --clean --distpath $dist --workpath (Join-Path $work 'backend') apps/desktop/specs/backend_service.spec
    Assert-LastExit 'Building backend_service.exe'
    & $python -m PyInstaller --noconfirm --clean --distpath $dist --workpath (Join-Path $work 'desktop') apps/desktop/specs/AICarScanner.spec
    Assert-LastExit 'Building AICarScanner.exe'

    $gui = Join-Path $dist 'AICarScanner.exe'
    $backend = Join-Path $dist 'backend_service.exe'
    foreach ($artifact in @($gui, $backend)) {
        if (-not (Test-Path $artifact) -or (Get-Item $artifact).Length -lt 100000) {
            throw "Missing or unexpectedly small compiled executable: $artifact"
        }
    }

    $iconFolder = Join-Path $dist 'icons'
    New-Item -ItemType Directory -Path $iconFolder -Force | Out-Null
    foreach ($icon in @('AI-Car-Scanner-master.png', 'AI-Car-Scanner-mobile.png', 'AI-Car-Scanner.webp', 'AI-Car-Scanner.ico')) {
        Copy-Item (Join-Path $root "assets\$icon") (Join-Path $iconFolder $icon) -Force
    }

    # In source mode this checks Pillow/Qt artwork parity and, on Windows,
    # the native icon embedded in the newly compiled GUI executable.
    $env:QT_QPA_PLATFORM = 'offscreen'
    $env:AI_CAR_VERIFY_EXE_PATH = $gui
    $env:AI_CAR_ICON_REPORT_PATH = Join-Path $dist 'desktop-icon-report.json'
    & $python apps/desktop/verify_icons.py
    Assert-LastExit 'Validating PNG/WEBP/ICO, Qt window icon and EXE icon'
    $report = Get-Content $env:AI_CAR_ICON_REPORT_PATH -Raw | ConvertFrom-Json
    if ($report.status -ne 'PASS') {
        throw "Icon smoke report is not PASS: $env:AI_CAR_ICON_REPORT_PATH"
    }

    @'
Desktop Icon Preview - Windows x64
==================================

1. Extract the COMPLETE ZIP. Keep AICarScanner.exe and backend_service.exe
   next to one another. Do NOT run AICarScanner.exe from inside the ZIP.
2. For a cloud API preview (optional), open PowerShell in this folder:
       $env:AI_CAR_BACKEND_URL = "https://ai-car-scaner.onrender.com"
       $env:AI_CAR_DISABLE_LLM_AUTOSTART = "1"
       .\AICarScanner.exe
3. Inspect the EXE icon in Explorer, taskbar icon, and actual window icon.
4. Also check icons/ and desktop-icon-report.json.

This build contains no GGUF model or llama-server executable. It can run
against a separately configured local service or the hosted API.

Verification only checks icon assets, Qt decoding, and the EXE's embedded
Windows icon. It does NOT prove that all GUI pages and backend flows work.
'@ | Set-Content -Path (Join-Path $dist 'README_ICON_PREVIEW.txt') -Encoding UTF8

    if (Test-Path $zip) { Remove-Item $zip -Force }
    Compress-Archive -Path (Join-Path $dist '*') -DestinationPath $zip -CompressionLevel Optimal -Force
    if (-not (Test-Path $zip)) { throw "ZIP packaging failed: $zip" }

    Write-Host "ICON PREVIEW BUILD: PASS"
    Write-Host "GUI: $gui"
    Write-Host "Backend: $backend"
    Write-Host "Verification: $env:AI_CAR_ICON_REPORT_PATH"
    Write-Host "ZIP: $zip"
}
finally {
    Remove-Item Env:AI_CAR_VERIFY_EXE_PATH -ErrorAction SilentlyContinue
    Remove-Item Env:AI_CAR_ICON_REPORT_PATH -ErrorAction SilentlyContinue
    Pop-Location
}
