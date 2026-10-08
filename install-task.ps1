# Registers a daily scheduled task that runs gh-pages-sync on Windows 10.
# Portable: uses the folder this script lives in, so the tool zip can be unzipped
# anywhere and this still points the task at the right place.
# Run in PowerShell as the user who owns the gh session (logged on):
#   powershell -ExecutionPolicy Bypass -File .\install-task.ps1
# To test immediately: Start-ScheduledTask -TaskName gh-pages-sync

$ErrorActionPreference = "Stop"

$TaskName = "gh-pages-sync"
$AppDir   = $PSScriptRoot
$Bat      = Join-Path $AppDir "run-sync.bat"
$Hour     = 6
$Minute   = 0

if (-not (Test-Path $Bat)) {
    Write-Error "run-sync.bat not found at $Bat"
}

$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$Bat`""
$trigger = New-ScheduledTaskTrigger -Daily -At (New-TimeSpan -Hours $Hour -Minutes $Minute)
# Interactive logon keeps gh's Credential-Manager token available to the task.
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Description "Mirror GitHub Pages build outputs via gh-pages-sync" -Force

Write-Host "Scheduled task '$TaskName' registered (daily at $('{0:D2}:{1:D2}' -f $Hour,$Minute))."
Write-Host "Tool folder: $AppDir"
Write-Host "Test now with: Start-ScheduledTask -TaskName $TaskName"