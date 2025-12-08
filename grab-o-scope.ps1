# grab-o-scope.ps1
# Simple script to easily run grab-o-scope.py with a user-friendly interface

do {
    # Ensure captures directory exists
    $capturesDir = Join-Path -Path (Get-Location) -ChildPath "captures"
    if (-not (Test-Path $capturesDir)) {
        New-Item -ItemType Directory -Path $capturesDir | Out-Null
    }
    # Prompt for base image name
    $baseName = Read-Host "Enter a base name for the image (e.g. example, capture, scope)"

    # Get current date and time in a safe filename format
    $timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
    $spacing = "_"
    $filename = "$baseName$spacing$timestamp.png"

    # Run the Python script
    Write-Host "Running: python grab_o_scope.py -v --auto_view --filename `".\captures\$filename`""
    python grab_o_scope.py -v --auto_view --filename ".\captures\$filename"

    Write-Host "================================================"
    # Ask if the user wants to run again
    $again = Read-Host "Do you want to grab another screenshot? (y/n)"
} while ($again -eq "y" -or $again -eq "Y" -or $again -eq "")
pause