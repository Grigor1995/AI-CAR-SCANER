$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$model = if ($env:LOCAL_LLM_MODEL_PATH) { $env:LOCAL_LLM_MODEL_PATH } else { Join-Path (Get-Location) "models\Qwen3-8B-Q4_K_M.gguf" }
if (-not (Test-Path $model)) { throw "GGUF model not found: $model" }

$hostName = if ($env:LOCAL_LLM_SERVER_HOST) { $env:LOCAL_LLM_SERVER_HOST } else { "127.0.0.1" }
$port = if ($env:LOCAL_LLM_SERVER_PORT) { [int]$env:LOCAL_LLM_SERVER_PORT } else { 8000 }
# 8192 is the default for this project so detailed live-data requests fit.
$context = if ($env:LOCAL_LLM_SERVER_CONTEXT) { [int]$env:LOCAL_LLM_SERVER_CONTEXT } else { 8192 }
$threads = if ($env:LOCAL_LLM_SERVER_THREADS) { [int]$env:LOCAL_LLM_SERVER_THREADS } else { 8 }
$exe = if ($env:LOCAL_LLM_SERVER_PATH) { $env:LOCAL_LLM_SERVER_PATH } else { (Get-Command llama-server.exe -ErrorAction SilentlyContinue).Source }
if (-not $exe) { throw "llama-server.exe not found. Set LOCAL_LLM_SERVER_PATH or add llama-server.exe to PATH." }

Write-Host "Starting llama-server: $exe"
Write-Host "Model: $model"
Write-Host "Endpoint: http://$hostName`:$port"
Write-Host "Context: $context"
& $exe -m $model -c $context -t $threads --host $hostName --port $port
