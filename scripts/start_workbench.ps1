$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
$env:PYTHONPATH = "$projectRoot/.runtime_packages;$projectRoot"
& "$projectRoot/.venv/Scripts/python.exe" -m uvicorn webapi.app:app --host 127.0.0.1 --port 8510

