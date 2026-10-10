# CycleNest GUI PowerShell Launcher
$Host.UI.RawUI.WindowTitle = "CycleNest Desktop GUI"
Write-Host "Starting CycleNest Graphical Application..." -ForegroundColor Magenta
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir
python gui.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`nAn error occurred. Check requirements: pip install -r requirements.txt" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
}
