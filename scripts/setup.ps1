$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $env:LOCALAPPDATA "Programs\Python\Python315\python.exe"
if (-not (Test-Path $py)) {
  throw "No encuentro Python 3.15 en $py. Instalá Python 3.15 y volvé a correr este script."
}

Push-Location (Join-Path $root "engine")
& $py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Pop-Location

Push-Location $root
npm install
npm install --prefix web
Pop-Location

Write-Host "Listo. Para la demo: npm run dev"
