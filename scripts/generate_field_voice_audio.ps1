# Synthetic fixture generation only; never uses customer recordings or a cloud TTS API.
param([Parameter(Mandatory=$true)][string]$OutputDirectory)
$ErrorActionPreference='Stop'
$taskRepository = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$taskFixtureRoot = [System.IO.Path]::GetFullPath((Join-Path $taskRepository '.local-data'))
$taskOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
if (-not $taskOutput.StartsWith($taskFixtureRoot+[System.IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output must be inside this checkout .local-data directory' }
Add-Type -AssemblyName System.Speech
$taskCases = Get-Content -LiteralPath (Join-Path $taskRepository 'tests/fixtures/field_voice_cases.json') -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Path $taskOutput -Force | Out-Null
$taskSynthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
$taskFormat = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(16000,[System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,[System.Speech.AudioFormat.AudioChannel]::Mono)
try {
 foreach ($taskCase in $taskCases) {
  $taskFile = Join-Path $taskOutput ($taskCase.id+'.wav')
  if (Test-Path -LiteralPath $taskFile) { throw 'Refusing to overwrite an existing fixture' }
  $taskSynthesizer.SetOutputToWaveFile($taskFile,$taskFormat)
  $taskSynthesizer.Speak($taskCase.text)
  $taskSynthesizer.SetOutputToNull()
 }
} finally { $taskSynthesizer.Dispose() }
Write-Output 'Generated ten synthetic WAV fixtures. These are not noisy-field or real-device acceptance.'
