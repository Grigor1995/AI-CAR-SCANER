$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$root = Get-Location
if (Test-Path (Join-Path $root '.venv\Scripts\python.exe')) {
    $py = Join-Path $root '.venv\Scripts\python.exe'
} elseif (Test-Path (Join-Path $root '.venv-desktop\Scripts\python.exe')) {
    $py = Join-Path $root '.venv-desktop\Scripts\python.exe'
} else {
    throw 'Python virtual environment not found. Run scripts\bootstrap_desktop.ps1 first.'
}

& $py -m pip install --upgrade pip setuptools wheel
& $py -m pip install -r requirements.txt
& $py -m pip install -r apps\desktop\requirements.txt
& $py -m pip install pyinstaller

if (Test-Path 'build') { Remove-Item -Recurse -Force 'build' }
if (Test-Path 'dist') { Remove-Item -Recurse -Force 'dist' }

$pyinstaller = Join-Path (Split-Path $py) 'pyinstaller.exe'
& $pyinstaller --noconfirm --clean apps\desktop\specs\backend_service.spec
& $pyinstaller --noconfirm --clean apps\desktop\specs\AICarScanner.spec

New-Item -ItemType Directory -Force -Path 'dist\AICarScanner\models' | Out-Null
Copy-Item 'dist\backend_service\backend_service.exe' 'dist\AICarScanner\backend_service.exe' -Force

$server = (Get-Command llama-server.exe -ErrorAction SilentlyContinue).Source
if ($server -and (Test-Path $server)) {
    Copy-Item $server 'dist\AICarScanner\llama-server.exe' -Force
    Write-Host 'Bundled llama-server.exe.'
} else {
    Write-Warning 'llama-server.exe not found on PATH; set LOCAL_LLM_SERVER_PATH before running the packaged app.'
}

Write-Host ''
Write-Host 'Standalone build:'
Write-Host '  dist\AICarScanner\AICarScanner.exe'
Write-Host '  dist\AICarScanner\backend_service.exe'
Write-Host '  dist\AICarScanner\llama-server.exe (when available)'
Write-Host '  dist\AICarScanner\models\<your GGUF>'
