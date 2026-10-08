"""Load defaults from ``gh-pages-sync.toml`` or ``[tool.gh-pages-sync]``.

The tool mirrors GitHub Actions build outputs for a set of repos. ``dest`` is
the local root each repo lands under; ``artifact`` is the default Actions
artifact name to download, overridable per repo.

Example ``gh-pages-sync.toml``::

    [gh-pages-sync]
    dest = "sites"
    artifact = "github-pages"
    repos = ["jame-louis/docker-101", "jame-louis/python-101"]

    [gh-pages-sync.repos."jame-louis/docker-101"]
    artifact = "site"
    subdir = "docker-101"

``subdir`` defaults to the repo name (the part after ``/``). CLI args win.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RepoSettings:
    artifact: str | None = None
    subdir: str | None = None


@dataclass
class Config:
    dest: Path = Path("sites")
    artifact: str = "github-pages"
    repos: dict[str, RepoSettings] = field(default_factory=dict)


def _toml(f: Path) -> dict | None:
    try:
        with f.open("rb") as fh:
            return tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return None


def _repo_name(repo: str) -> str:
    return repo.rsplit("/", 1)[-1]


def _parse_section(section: dict, cfg: Config, sources: list[Path], f: Path) -> None:
    dest = section.get("dest")
    if isinstance(dest, str):
        cfg.dest = Path(os.path.expanduser(dest))
        sources.append(f)
    artifact = section.get("artifact")
    if isinstance(artifact, str) and artifact:
        cfg.artifact = artifact

    # Flat list form: repos = ["owner/a", "owner/b"]
    flat = section.get("repos")
    if isinstance(flat, list):
        for item in flat:
            if isinstance(item, str) and item:
                cfg.repos.setdefault(item, RepoSettings())

    # Per-repo table form: [repo-settings.repos."owner/a"] {artifact=..., subdir=...}
    per_repo = section.get("repos")
    if isinstance(per_repo, dict):
        for repo, overrides in per_repo.items():
            if not isinstance(overrides, dict):
                continue
            settings = cfg.repos.setdefault(repo, RepoSettings())
            art = overrides.get("artifact")
            if isinstance(art, str) and art:
                settings.artifact = art
            sub = overrides.get("subdir")
            if isinstance(sub, str) and sub:
                settings.subdir = sub

    # `subdir` defaults are resolved lazily (repo name) in cli.


def load(start: Path | None = None) -> Config:
    cfg = Config()
    sources: list[Path] = []
    cwd = Path(start or Path.cwd()).resolve()

    cur = cwd
    while True:
        for name in ("gh-pages-sync.toml", "pyproject.toml"):
            f = cur / name
            data = _toml(f)
            if not data:
                continue
            section = data.get("tool", {}).get("gh-pages-sync") if isinstance(
                data.get("tool"), dict) else None
            if section is None:
                section = data.get("gh-pages-sync")
            if isinstance(section, dict):
                _parse_section(section, cfg, sources, f)
        if cur.parent == cur:
            break
        cur = cur.parent

    cfg._sources = sources  # type: ignore[attr-defined]
    return cfg