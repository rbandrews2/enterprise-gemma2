param(
    [string]$BrowserKeyFile = (Join-Path $PSScriptRoot '..\.local-data\credentials\wzos-v2-browser-key.txt')
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Create the local Python virtual environment first.' }
if (-not (Test-Path -LiteralPath $BrowserKeyFile)) { throw 'Browser key file is missing. Supply -BrowserKeyFile with the downloaded V2 browser key file.' }
$browserKey = [IO.File]::ReadAllText((Resolve-Path -LiteralPath $BrowserKeyFile).Path).Trim()
if ($browserKey -notmatch '^AIza[0-9A-Za-z_-]{35}$') { throw 'Browser key file does not contain a valid Google API key format.' }
$previousKey = $env:WZOS_GOOGLE_MAPS_BROWSER_KEY
try {
    $env:WZOS_GOOGLE_MAPS_BROWSER_KEY = $browserKey
    Push-Location $repoRoot
    try {
        & $python -m uvicorn services.v2.app:create_app --factory --host 127.0.0.1 --port 8081 --no-proxy-headers
    } finally { Pop-Location }
} finally {
    $env:WZOS_GOOGLE_MAPS_BROWSER_KEY = $previousKey
    $browserKey = $null
}
