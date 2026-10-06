$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

$repo = Get-Location
$py = $null
if (Test-Path (Join-Path $repo '.venv\Scripts\python.exe')) {
    $py = (Join-Path $repo '.venv\Scripts\python.exe')
} elseif (Test-Path (Join-Path $repo '.venv-desktop\Scripts\python.exe')) {
    $py = (Join-Path $repo '.venv-desktop\Scripts\python.exe')
} else {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) { throw 'Python was not found in PATH.' }
    $py = (Join-Path $repo '.venv\Scripts\python.exe')
    & $pythonCmd.Source -m venv (Join-Path $repo '.venv')
}

& $py -m pip install --upgrade pip setuptools wheel
& $py -m pip install -r requirements.txt

Write-Host 'Desktop environment is ready.' -ForegroundColor Green
Write-Host 'Run: python -m apps.desktop.main'
