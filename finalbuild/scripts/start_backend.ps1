$ErrorActionPreference = 'Stop'
Set-Location "$PSScriptRoot\.."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python was not found in PATH." }
$env:PYTHONPATH = (Join-Path (Get-Location) 'backend')
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
