# run_gui.ps1
# Script to launch the Grab-O-Scope GUI using pipenv

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

Write-Host "Launching Grab-O-Scope GUI..." -ForegroundColor Green
$mainPyPath = Join-Path $scriptDir "src\main.py"
pipenv run python $mainPyPath
