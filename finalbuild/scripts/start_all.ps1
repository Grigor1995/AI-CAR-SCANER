$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { throw "Python was not found in PATH. Activate your virtual environment first." }

$env:PYTHONPATH = Join-Path (Get-Location) "backend"
$env:AI_CAR_BACKEND_HOST = if ($env:AI_CAR_BACKEND_HOST) { $env:AI_CAR_BACKEND_HOST } else { "127.0.0.1" }
$env:AI_CAR_BACKEND_PORT = if ($env:AI_CAR_BACKEND_PORT) { $env:AI_CAR_BACKEND_PORT } else { "8001" }
$env:LOCAL_LLM_SERVER_HOST = if ($env:LOCAL_LLM_SERVER_HOST) { $env:LOCAL_LLM_SERVER_HOST } else { "127.0.0.1" }
$env:LOCAL_LLM_SERVER_PORT = if ($env:LOCAL_LLM_SERVER_PORT) { $env:LOCAL_LLM_SERVER_PORT } else { "8000" }
$env:LOCAL_LLM_SERVER_URL = if ($env:LOCAL_LLM_SERVER_URL) { $env:LOCAL_LLM_SERVER_URL } else { "http://127.0.0.1:8000" }
$env:LOCAL_LLM_SERVER_TIMEOUT_S = if ($env:LOCAL_LLM_SERVER_TIMEOUT_S) { $env:LOCAL_LLM_SERVER_TIMEOUT_S } else { "300" }

& $py.Source -m apps.desktop.main
