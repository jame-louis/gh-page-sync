"""Command-line entry point for gh-pages-sync."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from gh_pages_sync import config as config_mod
from gh_pages_sync import runner, serve as serve_mod

# Internal state dir under dest; hidden from `serve` (dotfile).
STATE_DIR = ".gh-pages-sync"


def _resolve_dest(arg: str | None, cfg: config_mod.Config) -> Path:
    return Path(os.path.expanduser(arg or str(cfg.dest)))


def _subdir(repo: str, settings: config_mod.RepoSettings) -> str:
    return settings.subdir or repo.rsplit("/", 1)[-1]


def _state_path(dest: Path, subdir: str) -> Path:
    return dest / STATE_DIR / f"{subdir}.json"


def _read_sha(path: Path) -> str | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data.get("head_sha") if isinstance(data, dict) else None


def _write_sha(path: Path, sha: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"head_sha": sha}), encoding="utf-8")


def _sync_repos(cfg: config_mod.Config, run_id: str | None = None, *, force: bool = False) -> int:
    failures = 0
    if not cfg.repos:
        print("no repos configured (set 'repos' in gh-pages-sync.toml)", file=sys.stderr)
        return 1
    for repo, settings in cfg.repos.items():
        artifact = settings.artifact or cfg.artifact
        subdir = _subdir(repo, settings)
        outdir = cfg.dest / subdir
        print(f"[{repo}] artifact={artifact} -> {outdir}")

        current = runner.latest_success_sha(repo)
        state = _state_path(cfg.dest, subdir)
        if not force and current and current == _read_sha(state):
            print(f"  unchanged (head {current[:7]}), skipping")
            continue

        res = runner.download(repo, artifact, outdir, run_id=run_id)
        if res.ok:
            if current:
                _write_sha(state, current)
            print(f"  ok: {res.files} file(s)")
        else:
            print(f"  ERROR: {res.error}", file=sys.stderr)
            failures += 1
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gh-pages-sync",
        description="Download GitHub Actions build outputs for a set of Pages "
        "repos into a local tree, and serve them locally.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_sync = sub.add_parser("sync", help="Download Actions build output for each configured repo.")
    p_sync.add_argument("--repo", action="append", default=[],
                        help="Add 'owner/repo' to sync (repeatable; skips default subdir naming).")
    p_sync.add_argument("--artifact", help="Artifact name override (default: from config).")
    p_sync.add_argument("--dest", help="Local root dir (default: from config).")
    p_sync.add_argument("--run-id", help="Only download from this specific run.")
    p_sync.add_argument("--force", action="store_true",
                        help="Re-download even if the build's commit is unchanged.")

    p_serve = sub.add_parser("serve", help="Serve a synced repo (or the dest root) locally.")
    p_serve.add_argument("sub", nargs="?", help="Repo subdir under dest (e.g. docker-101).")
    p_serve.add_argument("--dest", help="Local root dir (default: from config).")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)

    args = parser.parse_args(argv)
    cfg = config_mod.load()
    dest = _resolve_dest(getattr(args, "dest", None), cfg)

    if args.command == "serve":
        directory = dest / args.sub if args.sub else dest
        serve_mod.serve(directory, host=args.host, port=args.port)
        return 0

    # sync
    cfg.dest = dest
    for repo in args.repo:
        cfg.repos.setdefault(repo, config_mod.RepoSettings())
    if args.artifact:
        cfg.artifact = args.artifact
    return _sync_repos(cfg, run_id=args.run_id, force=args.force)