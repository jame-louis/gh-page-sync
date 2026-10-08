# 2026-10-08 — Package as downloadable Windows tool

Built on the 2026-10-07 refactor: freeze the CLI to a single Windows exe and
ship it as a zip. Windows box keeps only `gh` as an external dep.

## Added
- `src/gh_pages_sync/__main__.py` (exe / `python -m` entry). Verified both
  `python -m gh_pages_sync` and the `gh-pages-sync` script entry run.
- `runner._find_gh()` — prefers `gh.exe` beside the frozen exe, else PATH.
  Enables a fully self-contained folder if the user drops gh.exe in.
- `.github/workflows/build-release.yml` — pip + PyInstaller onefile on
  windows-latest; zips exe + `run-sync.bat` + `install-task.ps1` +
  `gh-pages-sync.toml` + `DIST-README.txt`; uploads run artifact; attaches to
  Release on `v*` tags (also `workflow_dispatch`).
- `DIST-README.txt`, `.gitignore`.

## Changed
- `run-sync.bat` → `%~dp0` + calls `gh-pages-sync.exe` (no uv).
- `install-task.ps1` → `$PSScriptRoot` (portable anywhere).

## Status
16 unit tests pass locally. The actual `.exe` build can only be confirmed by
running the workflow on GitHub (no Windows available here) — that is the open
verification item. Living docs:
`journey/plans/2026-10-08-gh-pages-sync-win-package.md`.