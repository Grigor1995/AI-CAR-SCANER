$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\..\.."
$root = Get-Location
if (Test-Path (Join-Path $root '.venv\Scripts\python.exe')) {
    $py = Join-Path $root '.venv\Scripts\python.exe'
} elseif (Test-Path (Join-Path $root '.venv-desktop\Scripts\python.exe')) {
    $py = Join-Path $root '.venv-desktop\Scripts\python.exe'
} else {
    throw 'Python virtual environment not found. Run scripts\bootstrap_desktop.ps1 first.'
}

& $py -m pip install -r requirements.txt
& $py -m pip install pyinstaller pillow
& $py apps\desktop\prepare_windows_icon.py
$pyinstaller = Join-Path (Split-Path $py) 'pyinstaller.exe'
& $pyinstaller --noconfirm --clean apps\desktop\specs\backend_service.spec
& $pyinstaller --noconfirm --clean apps\desktop\specs\AICarScanner.spec
Write-Host 'Built: dist\AICarScanner'
