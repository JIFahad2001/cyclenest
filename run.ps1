# CycleNest PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "CycleNest Console"
Write-Host "Starting CycleNest Menstrual Tracker..." -ForegroundColor Magenta
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
python main.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nAn error occurred. Check requirements: pip install rich" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
}
