# gh-pages-sync — Refactor to `gh run download`

Date: 2026-10-07
Replaces: `journey/plans/2026-10-07-gh-pages-sync.md` (the crawl-based design)

## Why the change

The user's real need is simple: *"download the GitHub Actions build output for a
set of Pages repos (jame-louis/docker-101, python-101, …)".* The live-site crawl
(py's `wget --mirror` style) is the wrong mechanism — it re-fetches HTML over
HTTP, needs a checksum store to prune, and duplicates what CI already produced.

Notes confirmed from investigation:

- These repos deploy with `actions/upload-pages-artifact` → `actions/deploy-pages`.
- Verified live: `gh run download -n github-pages` DOES return the output, as a
  single `artifact.tar` (the Pages deployment artifact — 63 MB / ~800 files for
  docker-101). The runner unpacks it. No workflow change is required; the
  default artifact name `github-pages` works out of the box.

## New architecture

Thin CLI. Zero runtime deps (stdlib + `gh` binary on PATH).

```
src/gh_pages_sync/
  __init__.py     main() entry
  config.py       dest root, default artifact, repo list (+ per-repo overrides)
  runner.py       wraps `gh run download` (subprocess), flatten, file count
  cli.py          `sync` (all/named repos) + `serve`
  serve.py        stdlib static preview server
```

Deleted: `crawl.py`, `store.py`, `httpclient.py`, `resolve.py`, `syncer.py`
and their tests. Drop the `requests` dependency.

## Config (`gh-pages-sync.toml` or `[tool.gh-pages-sync]` in pyproject)

```toml
[gh-pages-sync]
dest = "sites"                 # root dir; each repo lands in dest/<subdir>
artifact = "github-pages"      # default artifact name
repos = ["jame-louis/docker-101", "jame-louis/python-101"]

[gh-pages-sync.repos."jame-louis/docker-101"]
artifact = "site"              # optional per-repo override
subdir  = "docker-101"         # optional; default = repo name
```

`subdir` defaults to the part after `/` in `owner/repo`.

## Behaviour

- `sync` — for each configured repo run
  `gh run download --repo <r> -n <artifact> --dir <dest>/<subdir>` (stdlib
  `subprocess.run`), then flatten the single artifact subdir up and count files.
  Reports per-repo ok/error; continues past failures.
- `serve [<subdir>]` — serve `<dest>/<subdir>` (default: dest root), hiding
  dotfiles.

## Scope decisions

- No incremental logic / checksum store — `gh run download` always fetches the
  latest artifact and overwrites, which matches "get the Actions output." This is
  deliberately simpler than the old engine.
- No Pages URL resolution, no sitemap/robots, no threading, no config-in-src.
- Artifact availability depends on the workflow uploading a persistent artifact;
  the tool reports a clean error when the artifact is absent.

## Implementation

1. Write `runner.py` (cmd builder + `download()` + flatten + count).
2. Rewrite `config.py` (repos dict, artifact, dest).
3. Rewrite `cli.py` + `serve.py`.
4. Delete obsolete modules and their tests; drop `requests`.
5. New tests: `runner` (cmd build, flatten, mocked download),
   `config` (parsing + subdir default), `cli` (sync iterates repos).
6. `uv run pytest`.