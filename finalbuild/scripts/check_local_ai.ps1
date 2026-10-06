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
& $py -c "from backend.ai.llm.factory import build_llm_provider; import json; p=build_llm_provider(); print(json.dumps(p.availability(), indent=2))"
