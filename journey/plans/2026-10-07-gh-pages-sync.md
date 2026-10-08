# gh-pages-sync — Design & Implementation Plan

Date: 2026-10-07

## Goal

A CLI tool that mirrors the latest **published** GitHub Pages content of a
given repo onto a local directory, keeping it in sync incrementally, so it can
be served/hosted locally (local deploy / fallback mirror).

## Decisions (confirmed with user)

- **Content source:** Mirror the *live* Pages site over HTTPS (reflects exactly
  what GitHub serves; works for private repos; no build toolchain needed).
- **History/versioning:** Checksum mirror. Local folder + a checksum store.
  Download only changed/new files; prune local files no longer on the site.
- **Runtime:** Python, dependency-managed with **uv** (installed: uv 0.11.24).

## Open trade-offs surfaced (addressed in design)

1. **No remote manifest.** GitHub Pages does NOT expose a directory listing, so
   the file set must be **discovered by crawling** the served HTML (a
   `wget --mirror`-style approach: follow `a[href]`, `link`, `script`, `img`,
   and rewrite/pin same-site, same-prefix resources). Trade-off vs.
   "build-from-source" (rejected): unlinked assets are missed, but what the
   site actually serves is preserved bit-for-bit.
2. **Discovery completeness:** Supplement the crawl with `sitemap.xml` /
   `robots.txt` seed URLs if present. `--full` flag re-crawls everything;
   otherwise skip crawls of already-collected URLs.
3. **Checksum store:** SQLite (stdlib `sqlite3`) rather than JSON — atomic,
   concurrency-safe, durable; one table keyed by relative path storing
   `sha256`, size, mtime.
4. **Custom domains:** resolve via the repo's `CNAME` file on default branch
   (raw.githubusercontent.com, no auth for public repos); fall back to
   `https://<owner>.github.io/<repo>/` (project site) or `https://<owner>.github.io/`
   (user/org site when repo matches `<owner>.github.io`).
5. **Project layout:** `src/`-layout Python package (uv default), zero runtime
   deps beyond `requests`; stdlib `html.parser` for link extraction;
   `concurrent.futures.ThreadPoolExecutor` for parallel downloads.
6. **Local deploy:** `serve` subcommand = stdlib `http.server` bound to a local
   port over the mirror directory.

## Scope / Commands

- `gh-pages-sync sync <owner>/<repo> [--dest <dir>] [--full] [--workers N] [--token ...]`
- `gh-pages-sync serve [--dir <dir>] [--port N]`
- `gh-pages-sync status [--dest <dir>]`
- `gh-pages-sync config` (optional; default repo/dest from `gh-pages.toml`/`pyproject`)

## Out of scope (v1)

- Build-from-source mode (deferred).
- Incremental `sitemap.xml`/robots extraction as hard requirement.
- Multi-site orchestration / scheduling (the user can cron `sync`).

## Implementation steps

1. Scaffold uv project (`uv init`, deps: `requests`; dev: `pytest`).
2. `resolve.py`: repo -> pages URL (CNAME via raw.githubusercontent, user vs project default).
3. `crawler.py`: HTML link extraction, URL normalization, same-site/same-prefix filter.
4. `store.py`: SQLite checksum store (add/update/read/prune).
5. `fetcher.py`: threaded GET, ETag/mtime/checksum compare, write to dest.
6. `serve.py`: local static server.
7. `cli.py`: argparse wiring + config loading.
8. Tests: curl-able fixtures for resolve/store/crawler; optional live smoke test.

## Verification

- Unit tests pass (`uv run pytest`).
- Live smoke: sync a small public Pages site into a temp dir, assert files land,
  re-run asserts no-op (idempotent), mutate a file, assert it re-downloads.