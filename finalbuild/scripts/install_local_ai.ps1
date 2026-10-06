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

& $py -m pip install --upgrade pip setuptools wheel
& $py -m pip install -r requirements.txt

Write-Host 'Python dependencies installed.' -ForegroundColor Green
Write-Host 'Local LLM runtime: standalone llama-server.exe (not a Python package).'
Write-Host 'Model: .\models\Qwen3-8B-Q4_K_M.gguf'
