# 2026-10-07 — Refactor to `gh run download`

## What changed
Replaced the crawl-based mirror engine with a thin `gh run download` wrapper:
- **Deleted** `crawl.py`, `store.py`, `httpclient.py`, `resolve.py`, `syncer.py`
  and their tests. Dropped the `requests` dependency (stdlib only now).
- **Added** `runner.py` (subprocess wrapper + normalize), rewrote `config.py`
  (dest/artifact/repo list), `cli.py` (`sync` + `serve`), `serve.py`.
- New tests: 14 passing (`uv run pytest`).

## Key discovery (was wrong before)
Had assumed `deploy-pages` consumed the artifact so nothing was downloadable.
**Live check proved otherwise:** `gh run download -n github-pages` for
`jame-louis/docker-101` returns the Pages deployment artifact as a single
`artifact.tar` (63 MB, ~800 files) containing the whole built site. The runner
unpacks it. So the tool works out of the box — no workflow edit needed.

Smoke test: `sync --repo jame-louis/docker-101` → `sites/docker-101/` = 790 files
(`index.html`, `_astro`, `lectures`, `slides`, …). Re-run is stable/overwrite.

## Config
`gh-pages-sync.toml` added with `dest=sites`, `artifact=github-pages`, and
repos `docker-101`, `python-101` (extendable). Per-repo `artifact`/`subdir`
overrides supported.

## Residual
`_flatten` handles both shapes: `upload-artifact` zip extracted into
`--dir/<name>/` (move dir up) and Pages deployment `artifact.tar` (extract in
place). Docstring/design updated to the corrected premise.