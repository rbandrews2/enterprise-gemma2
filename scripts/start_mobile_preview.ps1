param(
    [ValidateSet(8081,8083)][int]$Port = 8083,
    [string]$PythonExecutable = '',
    [switch]$Stop
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$launcher = Join-Path $PSScriptRoot 'run_mobile_preview.py'
$stateDirectory = Join-Path $projectRoot '.local-data/mobile-simulator'
$statePath = Join-Path $stateDirectory "server-$Port.json"
$url = "http://127.0.0.1:$Port/__simulator"

if ($Stop) {
    if (!(Test-Path -LiteralPath $statePath)) { Write-Output 'No saved simulator process.'; return }
    $state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    # A Windows virtualenv redirector may keep a separate listening Python child.
    $listener = @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
    $targetId = [int]$state.pid
    if ($listener.Count -eq 1) { $targetId = [int]$listener[0].OwningProcess }
    if ($listener.Count -gt 1) { throw 'Multiple listeners found. No process was stopped.' }
    $process = Get-CimInstance Win32_Process -Filter "ProcessId=$targetId"
    if (!$process) { Write-Output 'Simulator already stopped.'; return }
    if (!$process.CommandLine -or !$process.CommandLine.Contains($launcher)) {
        throw 'The saved process ID no longer belongs to this simulator. No process was stopped.'
    }
    Stop-Process -Id $targetId
    Write-Output 'Simulator stopped.'
    return
}

function Test-Simulator {
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec 2 -UseBasicParsing
        return $response.StatusCode -eq 200 -and $response.Content.Contains('WZOS mobile workspace')
    } catch { return $false }
}
if (Test-Simulator) { Write-Output "SIMULATOR_READY $url"; return }
$listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($listener) { throw "Port $Port belongs to another listener. It was not stopped. Choose the other preview port." }

if (!$PythonExecutable) {
    $workspaceRoot = Split-Path (Split-Path $projectRoot -Parent) -Parent
    $candidate = Join-Path $workspaceRoot '.venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $candidate) { $PythonExecutable = $candidate }
    else { $PythonExecutable = (Get-Command python -ErrorAction Stop).Source }
}
New-Item -ItemType Directory -Path $stateDirectory -Force | Out-Null
$runId = [guid]::NewGuid().ToString('N').Substring(0,8)
$stdoutPath = Join-Path $stateDirectory "server-$runId.out.log"
$stderrPath = Join-Path $stateDirectory "server-$runId.err.log"
$serverProcess = Start-Process -FilePath $PythonExecutable -ArgumentList @('-u', ('"' + $launcher + '"'), '--port', "$Port") -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath -PassThru
@{pid=$serverProcess.Id; port=$Port; url=$url; stdout=$stdoutPath; stderr=$stderrPath; started_at=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding utf8
$deadline = [DateTime]::UtcNow.AddSeconds(45)
while ([DateTime]::UtcNow -lt $deadline) {
    if (Test-Simulator) { Write-Output "SIMULATOR_READY $url"; return }
    $serverProcess.Refresh()
    if ($serverProcess.HasExited) {
        Get-Content -LiteralPath $stderrPath -Tail 10
        throw 'Simulator exited before becoming ready.'
    }
    Start-Sleep -Milliseconds 500
}
Write-Output "SIMULATOR_STARTING pid=$($serverProcess.Id); logs=$stderrPath"
