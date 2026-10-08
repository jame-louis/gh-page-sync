@echo off
setlocal
REM Scheduled action for gh-pages-sync on Windows 10 (Task Scheduler).
REM This batch file lives in the distributed tool folder and invokes the
REM bundled gh-pages-sync.exe next to it (no Python/uv/repo checkout needed).
REM Requires: the gh CLI on PATH (or a gh.exe placed next to it) and a
REM gh-pages-sync.toml in this same folder.

set "APP=%~dp0"
set "EXE=%APP%gh-pages-sync.exe"

if not exist "%EXE%" (
  echo [gh-pages-sync] gh-pages-sync.exe not found next to run-sync.bat>&2
  exit /b 1
)

cd /d "%APP%"
echo === [%date% %time%] sync start ===>> "%APP%sync.log"
"%EXE%" sync>> "%APP%sync.log" 2>&1
set "EC=%ERRORLEVEL%"
echo === [%date% %time%] sync exit=%EC% ===>> "%APP%sync.log"
exit /b %EC%