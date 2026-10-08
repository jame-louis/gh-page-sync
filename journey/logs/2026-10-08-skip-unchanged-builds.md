# 2026-10-08 — Skip unchanged builds (idempotent sync)

## What changed
`sync` now compares the repo's newest successful run `head_sha` (via
`gh run list --json databaseId,headSha,conclusion`) against a per-repo state
file (`<dest>/.gh-pages-sync/<subdir>.json`) and skips `gh run download` when
they match. `--force` re-downloads regardless.

- `runner.latest_success_sha()` + `_pick_success_sha()` — pure, testable.
- `cli` `_read_sha`/`_write_sha`/`_state_path` + skip branch.
- Unknown sha (no gh / no successful run / parse fail) → download anyway
  (never silently skip).

## Verified live (jame-louis/docker-101 + python-101)
1. First run: downloaded 790 + 260 files, recorded head SHAs.
2. Re-run: `unchanged (head …), skipping` for both — no download.
3. `--force`: re-downloaded both.
21 unit tests pass.

Also confirmed **python-101 syncs with the default `github-pages` artifact** —
the open question from `2026-10-07-gh-run-download-sync.md` is resolved.

## Interaction with the shipped zip
The rebuild distributes the new binary automatically on the next `v*` tag; the
state file lives under `dest/` (outside the served site), so it does not pollute
the mirror and is hidden by `serve`.