"""Tests for the ``gh run download`` wrapper (no real network)."""

import subprocess
import tarfile
from pathlib import Path
from unittest import mock

from gh_pages_sync import runner


def test_build_cmd_basic():
    argv = runner.build_cmd("jame-louis/docker-101", "site", Path("/tmp/out"))
    assert argv == [
        "gh", "run", "download",
        "--repo", "jame-louis/docker-101",
        "--name", "site",
        "--dir", "/tmp/out",
    ]


def test_build_cmd_with_run_id():
    argv = runner.build_cmd("o/r", "github-pages", Path("x"), run_id=123)
    assert argv[3] == "123"
    assert "--repo" in argv


def test_flatten_moves_single_artifact_dir_up(tmp_path):
    art = tmp_path / "site"
    (art / "nested").mkdir(parents=True)
    (art / "index.html").write_text("<h1>hi</h1>")
    (art / "nested" / "a.css").write_text("body{}")
    runner._flatten(tmp_path)
    assert (tmp_path / "index.html").exists()
    assert (tmp_path / "nested" / "a.css").exists()
    assert not (tmp_path / "site").exists()


def test_flatten_extracts_pages_deployment_tar(tmp_path):
    # A Pages deployment comes down as a single artifact.tar of the site.
    (tmp_path / "index.html").write_text("<h1>hi</h1>")
    with tarfile.open(tmp_path / "artifact.tar", "w") as tf:
        tf.add(tmp_path / "index.html", arcname="index.html")
    (tmp_path / "index.html").unlink()

    runner._flatten(tmp_path)
    assert (tmp_path / "index.html").exists()
    assert not (tmp_path / "artifact.tar").exists()


def test_flatten_keeps_multiple_dirs(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "x").write_text("1")
    runner._flatten(tmp_path)
    assert (tmp_path / "a").is_dir()
    assert (tmp_path / "b").is_dir()


@mock.patch("gh_pages_sync.runner.shutil.which", return_value="/usr/bin/gh")
@mock.patch("gh_pages_sync.runner.subprocess.run")
def test_download_extracts_into_outdir(mock_run, mock_which, tmp_path):
    # gh places the artifact under outdir/<name>/...
    art = tmp_path / "out" / "site"
    art.mkdir(parents=True)
    (art / "index.html").write_text("<h1>hi</h1>")
    (art / "app.css").write_text("body{}")

    mock_run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")

    res = runner.download("jame-louis/docker-101", "site", tmp_path / "out")
    assert res.ok
    assert res.files == 2
    # Flattened: files sit directly under out/, not out/site/.
    assert (tmp_path / "out" / "index.html").exists()
    assert not (tmp_path / "out" / "site").exists()
    # The gh binary we claimed to find was used.
    cmd = mock_run.call_args.args[0]
    assert cmd[:3] == ["gh", "run", "download"]


@mock.patch("gh_pages_sync.runner.shutil.which", return_value=None)
def test_download_missing_gh(mock_which):
    res = runner.download("o/r", "github-pages", Path("x"))
    assert not res.ok
    assert "not found" in (res.error or "").lower()


def test_find_gh_prefers_local_gh_exe(tmp_path, monkeypatch):
    # A gh.exe beside the executable wins over any PATH lookup.
    exe = tmp_path / "gh-pages-sync.exe"
    local_gh = tmp_path / "gh.exe"
    local_gh.touch()
    monkeypatch.setattr(runner.sys, "executable", str(exe))
    monkeypatch.setattr(runner.sys, "frozen", True, raising=False)
    monkeypatch.setattr(runner, "shutil", mock.MagicMock())  # must not hit PATH
    assert runner._find_gh() == str(local_gh)


def test_find_gh_falls_back_to_path():
    with mock.patch("gh_pages_sync.runner.shutil.which", return_value="/usr/bin/gh"):
        assert runner._find_gh() == "/usr/bin/gh"


def test_pick_success_sha_returns_newest_success():
    records = [
        {"databaseId": 2, "headSha": "abc", "conclusion": "failure"},
        {"databaseId": 3, "headSha": "def", "conclusion": "success"},
        {"databaseId": 4, "headSha": "ghi", "conclusion": "success"},
    ]
    assert runner._pick_success_sha(records) == "def"


def test_pick_success_sha_none_when_no_success():
    assert runner._pick_success_sha([{"headSha": "x", "conclusion": "failure"}]) is None
    assert runner._pick_success_sha([]) is None