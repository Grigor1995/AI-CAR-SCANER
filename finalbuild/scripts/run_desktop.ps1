$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$repo = Get-Location
if (Test-Path (Join-Path $repo '.venv\Scripts\python.exe')) {
    $py = Join-Path $repo '.venv\Scripts\python.exe'
} elseif (Test-Path (Join-Path $repo '.venv-desktop\Scripts\python.exe')) {
    $py = Join-Path $repo '.venv-desktop\Scripts\python.exe'
} else {
    throw 'Python virtual environment not found. Run scripts\bootstrap_desktop.ps1 first.'
}
$env:PYTHONPATH = Join-Path $repo 'backend'
& $py -m apps.desktop.main
