"""Tests for config parsing (dest, artifact, repo list + per-repo overrides)."""

import tomllib
from pathlib import Path

from gh_pages_sync import config


def _load(toml: str, path: str = "gh-pages-sync.toml") -> config.Config:
    f = Path(path)
    f.write_text(toml)
    return config.load(Path("."))


def test_flat_repos_list(tmp_path):
    parsed = tomllib.loads(
        "[gh-pages-sync]\n"
        "dest = \"sites\"\n"
        "artifact = \"github-pages\"\n"
        "repos = [\"jame-louis/docker-101\", \"jame-louis/python-101\"]\n"
    )
    cfg = config.Config()
    config._parse_section(parsed["gh-pages-sync"], cfg, [], tmp_path / "gh-pages-sync.toml")
    assert str(cfg.dest) == "sites"
    assert cfg.artifact == "github-pages"
    assert set(cfg.repos) == {"jame-louis/docker-101", "jame-louis/python-101"}


def test_per_repo_overrides():
    parsed = tomllib.loads(
        "[gh-pages-sync]\n"
        "[gh-pages-sync.repos.\"jame-louis/docker-101\"]\n"
        "artifact = \"site\"\n"
        "subdir = \"docker-101\"\n"
        "[gh-pages-sync.repos.\"jame-louis/python-101\"]\n"
    )
    cfg = config.Config()
    config._parse_section(parsed["gh-pages-sync"], cfg, [], Path("x"))
    s = cfg.repos["jame-louis/docker-101"]
    assert s.artifact == "site"
    assert s.subdir == "docker-101"
    assert cfg.repos["jame-louis/python-101"].artifact is None


def test_missing_config_defaults(tmp_path):
    cfg = config.load(tmp_path)
    assert cfg.dest == Path("sites")
    assert cfg.artifact == "github-pages"
    assert cfg.repos == {}


def test_no_config_does_not_crash_on_walk():
    # load() walks up from cwd; on a dir with no config it must not set repos.
    cfg = config.load(Path("/"))
    assert cfg.repos == {}