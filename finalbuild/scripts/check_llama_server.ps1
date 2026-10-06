$ErrorActionPreference = "Stop"
$url = if ($env:LOCAL_LLM_SERVER_URL) { $env:LOCAL_LLM_SERVER_URL } else { "http://127.0.0.1:8000" }
try {
  $health = Invoke-RestMethod "$url/health" -TimeoutSec 5
  $models = Invoke-RestMethod "$url/v1/models" -TimeoutSec 5
  [pscustomobject]@{
    available = $true
    health = $health
    models = $models.data
  } | ConvertTo-Json -Depth 10
} catch {
  [pscustomobject]@{ available = $false; error = $_.Exception.Message } | ConvertTo-Json -Depth 5
  exit 1
}
