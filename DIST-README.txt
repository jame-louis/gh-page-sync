gh-pages-sync — mirror GitHub Pages build outputs on Windows 10
================================================================

This folder is a self-contained Windows tool. No Python, no uv, and no repo
checkout are needed to run the scheduled sync.

Contains
--------
  gh-pages-sync.exe    the tool (standalone; built with PyInstaller)
  run-sync.bat         what Task Scheduler runs each day
  install-task.ps1     registers the daily scheduled task
  gh-pages-sync.toml   which repos to sync and where (EDIT THIS)
  sync.log             created on first run; check it if a sync "didn't happen"

One requirement: the GitHub CLI (gh). It is used to download build artifacts.
  winget install GitHub.cli
  gh auth login                  # choose your account (username/HTTPS)
Drop gh.exe next to this folder too if you prefer it to any global install.

Setup
-----
1. Edit gh-pages-sync.toml: set the repos (and optional dest/artifact) you want.
2. Run the task installer once (PowerShell, logged on as the gh user):
       powershell -ExecutionPolicy Bypass -File .\install-task.ps1
3. Test immediately:
       Start-ScheduledTask -TaskName gh-pages-sync
4. Confirm output under sites\ (next to gh-pages-sync.toml, via sync.log).

The task runs daily at 06:00 while you are logged on (gh keeps its token in
the Windows Credential Manager, available only when a user is logged on). To
change the time, edit the $Hour / $Minute lines in install-task.ps1.

Manual run anytime:
       gh-pages-sync.exe sync
       gh-pages-sync.exe sync --repo jame-louis/docker-101