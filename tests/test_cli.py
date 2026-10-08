"""Tests for the CLI wiring (repo list -> one download per repo)."""

from unittest import mock

from gh_pages_sync import config as config_mod
from gh_pages_sync import cli, runner


def test_subdir_defaults_to_repo_name():
    assert cli._subdir("jame-louis/docker-101", config_mod.RepoSettings()) == "docker-101"


def test_subdir_uses_override():
    s = config_mod.RepoSettings(subdir="custom")
    assert cli._subdir("owner/repo", s) == "custom"


def test_sync_calls_download_for_each_repo(tmp_path, capsys):
    cfg = config_mod.Config()
    cfg.dest = tmp_path
    cfg.repos = {
        "jame-louis/docker-101": config_mod.RepoSettings(),
        "jame-louis/python-101": config_mod.RepoSettings(artifact="site"),
    }
    results = [
        runner.DownloadResult("jame-louis/docker-101", True, files=5),
        runner.DownloadResult("jame-louis/python-101", False, error="artifact not found"),
    ]
    with mock.patch("gh_pages_sync.runner.download", side_effect=results) as dl:
        code = cli._sync_repos(cfg)

    assert code == 1  # one repo failed
    assert dl.call_count == 2
    args0 = dl.call_args_list[0].args
    assert args0[0] == "jame-louis/docker-101"
    captured = capsys.readouterr()
    assert "docker-101" in captured.out and "python-101" in captured.out
    assert "artifact not found" in captured.err