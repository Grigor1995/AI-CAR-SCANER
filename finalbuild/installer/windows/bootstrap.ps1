param(
    [Parameter(Mandatory=$true)][string]$Root,
    [string]$Manifest,
    [string]$Helper,
    [switch]$WithAI,
    [string]$LocalModel,
    [string]$SourceArchive,
    [string]$ErrorFile,
    [switch]$CheckRunning
)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
function Save-SetupError([string]$Message) {
    if ($ErrorFile) {
        try { [IO.File]::WriteAllText($ErrorFile, $Message, (New-Object Text.UTF8Encoding($false))) } catch { }
    }
    try {
        $folder = Join-Path $env:LOCALAPPDATA 'AI-Car-Scanner\installer-logs'
        New-Item -ItemType Directory -Force -Path $folder | Out-Null
        [IO.File]::WriteAllText((Join-Path $folder 'last-error.txt'), $Message, (New-Object Text.UTF8Encoding($false)))
    } catch { }
}
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
$transcribing = $false
try {
    if ($ErrorFile) { Remove-Item -LiteralPath $ErrorFile -ErrorAction SilentlyContinue }
    if (-not $CheckRunning) {
        try {
            $folder = Join-Path $env:LOCALAPPDATA 'AI-Car-Scanner\installer-logs'
            New-Item -ItemType Directory -Force -Path $folder | Out-Null
            $log = Join-Path $folder ('bootstrap-' + (Get-Date -Format 'yyyyMMddTHHmmssfff') + '.log')
            Start-Transcript -Path $log | Out-Null
            $transcribing = $true
        } catch { }
    }
    $repositoryPath = (Join-Path $Root 'repo').TrimEnd('\') + '\'
    $running = @()
    if (Test-Path -LiteralPath (Join-Path $Root 'repo')) {
        $running = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='llama-server.exe'" | Where-Object {
        ($_.ExecutablePath -and $_.ExecutablePath.StartsWith($repositoryPath, [StringComparison]::OrdinalIgnoreCase)) -or
        ($_.CommandLine -and $_.CommandLine.IndexOf($repositoryPath, [StringComparison]::OrdinalIgnoreCase) -ge 0)
        })
    }
    if ($running.Count -gt 0) {
        Save-SetupError 'Close AI Car Scanner and its backend/local AI before updating or uninstalling.'
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
    if ($LocalModel) { $arguments += @('--model', $LocalModel) }
    if ($SourceArchive) { $arguments += @('--source-archive', $SourceArchive) }
    if ($ErrorFile) { $arguments += @('--error-file', $ErrorFile) }
    & $python @arguments
    if ($LASTEXITCODE -ne 0) {
        if ($ErrorFile -and (Test-Path -LiteralPath $ErrorFile)) {
            throw ([IO.File]::ReadAllText($ErrorFile, [Text.Encoding]::UTF8))
        }
        throw "Application setup failed ($LASTEXITCODE). Logs: $Root\logs"
    }
    exit 0
} catch {
    Save-SetupError $_.Exception.Message
    Write-Host $_ -ForegroundColor Red
    Write-Host 'Setup did not complete. Keep this error message and retry Setup.'
    exit 1
} finally {
    if ($transcribing) { try { Stop-Transcript | Out-Null } catch { } }
}
