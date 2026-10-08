# 2026-10-08 — Fix "artifact.tar: file exists" on repeat downloads (Windows)

## Symptom (from the scheduled box's sync.log)
```
ERROR: error downloading github-pages: error extracting zip archive:
error extracting "artifact.tar": openat artifact.tar: file exists
```
First run OK; subsequent runs failed (intermittent, sometimes partially).

## Root cause
`gh run download` extracts the Pages artifact into the target dir as
`artifact.tar`. On re-runs into a **non-empty** target, `gh`'s no-overwrite
extractor refuses: `openat artifact.tar: file exists`. Whether the stale file
lingers depends on prior extraction state → intermittent per-repo.

## Fix
`runner.download()` now downloads into a sibling temp dir
(`.<name>.tmp-<pid>`), flattens + counts there, then swaps it into place
(rmtree old outdir, rename). `gh` always extracts into an empty tree, so
repeat downloads are clean and atomic-ish. Temp dir cleaned on failure too.

## Verified (live, macOS)
- Two consecutive `--force` runs into the same populated `dest` both succeeded
  (docker-101 790 / python-101 260 files), no errors, no leftover `.tmp-*`.
- 22 unit tests pass (added swap + stale-outdir replacement tests).

## Note
The shipped release zip (v0.1.0) predates this fix and the idempotent-skip
feature (`journey/logs/2026-10-08-skip-unchanged-builds.md`). Both need a new
`v*` tag to rebuild/republish the tool for the Windows box.