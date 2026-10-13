$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$root = (Get-Location).Path

if (Test-Path (Join-Path $root '.venv\Scripts\python.exe')) {
    $py = Join-Path $root '.venv\Scripts\python.exe'
} elseif (Test-Path (Join-Path $root '.venv-desktop\Scripts\python.exe')) {
    $py = Join-Path $root '.venv-desktop\Scripts\python.exe'
} else {
    throw 'Python virtual environment not found. Run scripts\bootstrap_desktop.ps1 first.'
}

& $py -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw 'Failed to update pip/setuptools/wheel.' }
& $py -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Failed to install root requirements.' }
& $py -m pip install -r apps\desktop\requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Failed to install Desktop requirements.' }
& $py -m pip install pyinstaller pillow
if ($LASTEXITCODE -ne 0) { throw 'Failed to install PyInstaller/Pillow.' }

# Do not wipe the existing dist/ directory; it may contain tracked or user-owned files.
# This builder owns only these isolated output directories.
$dist = Join-Path $root 'dist-release'
$work = Join-Path $root 'build-release'
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
if (Test-Path $work) { Remove-Item -Recurse -Force $work }
New-Item -ItemType Directory -Force -Path $dist | Out-Null

$pyinstaller = Join-Path (Split-Path $py) 'pyinstaller.exe'
& $pyinstaller --noconfirm --clean --distpath $dist --workpath (Join-Path $work 'backend-service') apps\desktop\specs\backend_service.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed while building backend_service.exe.' }
& $pyinstaller --noconfirm --clean --distpath $dist --workpath (Join-Path $work 'desktop') apps\desktop\specs\AICarScanner.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed while building AICarScanner.exe.' }

New-Item -ItemType Directory -Force -Path (Join-Path $dist 'models') | Out-Null
$server = (Get-Command llama-server.exe -ErrorAction SilentlyContinue).Source
if ($server -and (Test-Path $server)) {
    Copy-Item $server (Join-Path $dist 'llama-server.exe') -Force
    Write-Host 'Bundled llama-server.exe.'
} else {
    Write-Warning 'llama-server.exe not found on PATH; set LOCAL_LLM_SERVER_PATH before running the packaged app.'
}

Write-Host ''
Write-Host 'Standalone build outputs:'
Write-Host "  $(Join-Path $dist 'AICarScanner.exe')"
Write-Host "  $(Join-Path $dist 'backend_service.exe')"
Write-Host "  $(Join-Path $dist 'llama-server.exe') (when available)"
Write-Host "  $(Join-Path $dist 'models\<your GGUF model file>')"
