param(
    [Parameter(Mandatory=$true)][string]$Root,
    [string]$Manifest,
    [string]$Helper,
    [switch]$WithAI,
    [switch]$CheckRunning
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
function Find-Python {
    $candidates = @()
    foreach ($name in @('py.exe', 'python.exe')) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            if ($name -eq 'py.exe') {
                try {
                    $path = & $command.Source -3 -c 'import sys; print(sys.executable)' 2>$null
                    if ($LASTEXITCODE -eq 0) { $candidates += $path }
                } catch { }
            } else { $candidates += $command.Source }
        }
    }
    foreach ($base in @('HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore')) {
        if (Test-Path $base) {
            foreach ($key in Get-ChildItem $base) {
                $install = Join-Path $key.PSPath 'InstallPath'
                if (Test-Path $install) {
                    $value = (Get-Item $install).GetValue('ExecutablePath')
                    if ($value) { $candidates += $value }
                }
            }
        }
    }
    foreach ($candidate in ($candidates | Select-Object -Unique)) {
        if ($candidate -match '\\Microsoft\\WindowsApps\\') { continue }
        if (Test-Path -LiteralPath $candidate) {
            try {
                & $candidate -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,12) and sys.maxsize > 2**32 else 1)' 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) { return $candidate }
            } catch { }
        }
    }
    return $null
}
try {
    $repositoryPath = (Join-Path $Root 'repo').TrimEnd('\') + '\'
    $running = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='llama-server.exe'" | Where-Object {
        ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($repositoryPath, [StringComparison]::OrdinalIgnoreCase)) -or
        ($_.CommandLine -and $_.CommandLine.IndexOf($repositoryPath, [StringComparison]::OrdinalIgnoreCase) -ge 0)
    })
    if ($running.Count -gt 0) {
        Write-Host 'Close AI Car Scanner and its backend/local AI before updating or uninstalling.' -ForegroundColor Red
        exit 10
    }
    if ($CheckRunning) { exit 0 }
    if (-not $Manifest -or -not $Helper) { throw 'Manifest and Helper are required for installation.' }
    $python = Find-Python
    if (-not $python) {
        Write-Host 'Downloading the latest stable Python 3.14 x64 installer from python.org...'
        $page = Invoke-WebRequest -UseBasicParsing 'https://www.python.org/downloads/windows/'
        $urls = [regex]::Matches($page.Content, 'https://www\.python\.org/ftp/python/(3\.14\.\d+)/python-3\.14\.\d+-amd64\.exe')
        if ($urls.Count -eq 0) { throw 'No stable Python 3.14 x64 installer found. Install Python 3.12+ x64 from python.org and retry.' }
        $url = ($urls | Sort-Object { [version]$_.Groups[1].Value } -Descending | Select-Object -First 1).Value
        $download = Join-Path $env:TEMP ('ai-car-python-' + [guid]::NewGuid().ToString() + '.exe')
        try {
            Invoke-WebRequest -UseBasicParsing $url -OutFile $download
            $signature = Get-AuthenticodeSignature -FilePath $download
            if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Python Software Foundation(?:,|$)') {
                throw 'Python installer publisher/signature verification failed.'
            }
            Write-Host 'Installing Python for this Windows user; no PATH changes.'
            $process = Start-Process -FilePath $download -ArgumentList '/quiet InstallAllUsers=0 PrependPath=0 Include_launcher=0 Include_test=0 Include_doc=0 Include_tcltk=0 AssociateFiles=0 Shortcuts=0' -PassThru -Wait
            if ($process.ExitCode -notin @(0,3010)) { throw "Python installer failed: $($process.ExitCode)" }
        } finally { Remove-Item -LiteralPath $download -Force -ErrorAction SilentlyContinue }
        $python = Find-Python
        if (-not $python) { throw 'Python was not detected after installation. Reopen Setup or install Python 3.12+ x64 manually.' }
    }
    $arguments = @($Helper, 'install', '--root', $Root, '--manifest', $Manifest)
    if ($WithAI) { $arguments += '--with-ai' }
    & $python @arguments
    if ($LASTEXITCODE -ne 0) { throw "Application setup failed ($LASTEXITCODE). Logs: $Root\logs" }
    exit 0
} catch {
    Write-Host $_ -ForegroundColor Red
    Write-Host 'Setup did not complete. Keep this error message and retry Setup.'
    # A visible console gives users the failure instead of disappearing immediately.
    Start-Sleep -Seconds 5
    exit 1
}
