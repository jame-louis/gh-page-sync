# gh-pages-sync — Package as a downloadable Windows tool

Date: 2026-10-08

## Goal
Turn the project into a self-contained Windows tool that can be *downloaded* and
configured — no repo clone, no Python install, no uv. The Windows 10 box then
only needs the `gh` CLI (for artifact auth/download) plus a scheduled task.

## Approach
- **Freeze the CLI to one exe** with PyInstaller (`--onefile`), entry point
  `src/gh_pages_sync/__main__.py` (`python -m gh_pages_sync`).
- **Build on Windows via GitHub Actions** (PyInstaller cannot cross-compile;
  we have no Windows box locally). Build on every `v*` tag **and** on manual
  `workflow_dispatch`; upload the zip as a run artifact; attach to a GitHub
  Release on tag builds.
- **Distribution zip** = `gh-pages-sync.exe` + `run-sync.bat` +
  `install-task.ps1` + `gh-pages-sync.toml` + `DIST-README.txt`.

## Windows-box experience (the polish)
1. `winget install GitHub.cli` && `gh auth login` (interactive; only external dep).
2. Download `gh-pages-sync-windows-x64.zip`, unzip anywhere.
3. Edit `gh-pages-sync.toml` (repos/dest/artifact).
4. `powershell -ExecutionPolicy Bypass -File .\install-task.ps1` → daily 06:00 task.

No Python/uv/repo clone on the target box.

## Key decisions
- **`gh` stays a dependency** (it is what talks to GitHub and keeps auth in the
  Windows Credential Manager). But `runner._find_gh()` prefers a `gh.exe` placed
  next to the tool, so you *can* ship a fully self-contained folder.
- Task still runs **interactive logon** so the Credential-Manager token is
  available; `install-task.ps1` uses `$PSScriptRoot` so it’s location-independent.
- `run-sync.bat` uses `%~dp0` and calls `gh-pages-sync.exe` directly — portable
  to wherever the zip is unzipped.

## Out of scope
- macOS/Linux exe (PyInstaller per-OS; could add jobs later).
- Bundling `gh.exe` into the zip by default (auth is interactive regardless;
  keep the zip small and a single global `gh` install).

## Changed/added files
- `src/gh_pages_sync/__main__.py` — exe/`-m` entry.
- `runner._find_gh()` — prefer local `gh.exe`, else PATH.
- `.github/workflows/build-release.yml` — Windows build + artifact + release.
- `run-sync.bat`, `install-task.ps1` — portable (exe-based).
- `DIST-README.txt`, `.gitignore`.

## Verification
- 16 unit tests pass (`uv run pytest`).
- `uv run python -m gh_pages_sync --help` works (the exe entry).
- Full Windows-exe build must be confirmed on CI (no local Windows).
- Also prior-iteration `journey/plans/2026-10-08-gh-pages-sync-windows.md`.