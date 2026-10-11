$ErrorActionPreference = "Stop"
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
$env:PYTHONPATH = $projectRoot

# Use the project environment when present; otherwise use the active Python.
# Install the documented dependencies first (README.md, Local workbench).
$python = Get-Command python -ErrorAction Stop | Select-Object -ExpandProperty Source
$venvPython = Join-Path $projectRoot ".venv/Scripts/python.exe"
if ($env:KHANYA_PYTHON) { $python = $env:KHANYA_PYTHON }
elseif (Test-Path $venvPython) { $python = $venvPython }
$port = 8510
if ($env:KHANYA_PORT) { $port = [int]$env:KHANYA_PORT }
& $python -m uvicorn webapi.app:app --host 127.0.0.1 --port $port
