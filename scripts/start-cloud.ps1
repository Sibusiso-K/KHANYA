param([int]$Port = 8766)
$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskEnv = Join-Path $taskRoot '.workbench/cloud.env'
if (-not (Test-Path -LiteralPath $taskEnv)) { throw 'Missing .workbench/cloud.env; configure SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY first.' }
foreach ($taskLine in Get-Content -LiteralPath $taskEnv) {
    if ($taskLine -match '^([A-Z_]+)=(.*)$') { [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process') }
}
$env:REEFPRINT_DEPLOYMENT = 'public'
Push-Location $taskRoot
try { & (Join-Path $taskRoot '.venv/Scripts/python.exe') -m uvicorn webapi.app:app --host 127.0.0.1 --port $Port }
finally { Pop-Location }
