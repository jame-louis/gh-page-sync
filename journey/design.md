# gh-pages-sync — Design snapshot

**Goal:** download the GitHub Actions build output for a configured set of
Pages repos into a local tree (`gh run download`), and serve it locally.

**Mechanism:** thin `gh run download` wrapper. No HTTP crawl, no checksum store.
The tool syncs `<dest>/<repo-name>/` for each repo from its Actions artifact.

**Discovery (2026-10-07):** `deploy-pages` does NOT make the output
undownloadable. `gh run download -n github-pages` for these repos returns the
Pages deployment artifact as a single `artifact.tar` (the whole built site); the
runner unpacks it. No workflow change is needed. The default artifact name
`github-pages` works; it's configurable per repo.

**Key decisions:**
- Runtime: Python 3.13, stdlib only (drop `requests`). Requires `gh` (on PATH
  or as `gh.exe` beside the tool).
- Config in `gh-pages-sync.toml` / `[tool.gh-pages-sync]`: `dest`, default
  `artifact`, `repos` list (+ per-repo `artifact`/`subdir` overrides).
- Always fetch latest artifact (no incremental store) — intentionally simple.

**Distribution:** frozen to a single Windows exe via PyInstaller, built by a
GitHub Actions `build-release.yml` (Windows job; `v*` tags → Release, also a
manual run → run artifact). Zip ships `gh-pages-sync.exe` + portable
`run-sync.bat` / `install-task.ps1` + config + `DIST-README.txt`, so a Win10 box
installs only `gh`, downloads the zip, edits config, and registers a daily task.
See `journey/plans/2026-10-08-gh-pages-sync-win-package.md`.

**History:** `journey/plans/2026-10-07-gh-run-download-sync.md` (refactor),
`journey/plans/2026-10-08-gh-pages-sync-windows.md` (scheduler), above (packaging).