# gh-pages-sync — Scheduled sync on Windows 10 (Task Scheduler)

Date: 2026-10-08

## Goal
Run `gh-pages-sync sync` automatically each day on a second Windows 10 PC, so
each configured repo's GitHub Actions build output stays mirrored in a local
folder without manual action.

## Runtime requirements on the Windows box
- **git** — to clone the repo (or ship it as a zip).
- **python / uv** — the project needs Python ≥ 3.13; `uv sync` will fetch a
  matching Python automatically if needed.
- **gh CLI** — `gh run download` does the work; must be authenticated as the
  account that owns the repos (`jame-louis`), scoped `repo`.
- **Network** — the box must be on and online when the task fires.
- **Path convention used below:** project at `C:\gh-pages-sync`. Adjust to taste.

## Steps
1. **Install uv** (admin PowerShell):
   `powershell -Command "irm https://astral.sh/uv/install.ps1 | iex"` \
   or `winget install astral-sh.uv`.
2. **Install gh**: `winget install GitHub.cli`, then `gh auth login`
   (authenticate as `jame-louis`, HTTPS, and keep the token local).
3. **Get the project**: `git clone https://github.com/jame-louis/gh-page-sync C:\gh-pages-sync`.
4. **Prepare**: `cd C:\gh-pages-sync` then `uv sync`
   (resolves Python + installs the package + dev deps). Confirm once manually:
   `uv run gh-pages-sync sync`.
5. **Create the scheduled task** (PowerShell, as the user who owns the gh
   session) — runs `run-sync.bat` daily at 06:00 while the user is logged on
   (so gh's stored token is available):
   ```powershell
   .\install-task.ps1
   ```
   Or point Task Scheduler's GUI (`taskschd.msc`) at `run-sync.bat`, daily.

## Files in this repo
- `run-sync.bat` — the scheduled action: cd into the project, run
  `uv run gh-pages-sync sync`, append a timestamped log to `sync.log`.
- `install-task.ps1` — creates the `gh-pages-sync` scheduled task (daily 06:00,
  interactive logon). `Start-ScheduledTask -TaskName gh-pages-sync` to test.
- `sync.log` — created on the box; check it first when a run "didn't happen".

## Auth / security notes
- Run the task as **your Windows user, only when logged on**. gh stores its
  token via the Windows Credential Manager; that store is unlocked only for a
  logged-on user. "Run whether user is logged on or not" would need a stored
  password AND would break gh's keyring unless a `GH_TOKEN` env is set on the
  task (storing a live token in the task definition is discouraged).
- The task runs with your live gh identity — scope the token to `repo` only.

## Idempotency
`gh run download` always fetches the latest output and overwrites, so frequent
scheduling is safe (no partial-state corruption). If downloads overlap with a
manual `sync`, both just re-download; the artifact fetch is atomic per repo.

## Logs
Plan the previous iteration on 2026-10-07 (`journey/plans/2026-10-07-gh-run-download-sync.md`);
those files stayed valid. This adds only the Windows scheduling layer.