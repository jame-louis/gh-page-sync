"""Tests for the CLI wiring (repo list -> one download per repo)."""

from unittest import mock

from gh_pages_sync import config as config_mod
from gh_pages_sync import cli, runner

OK_SHA = "1111111111111111111111111111111111111111"


def _repo_cfg(tmp_path, repos=("jame-louis/docker-101",)) -> config_mod.Config:
    cfg = config_mod.Config()
    cfg.dest = tmp_path
    cfg.repos = {r: config_mod.RepoSettings() for r in repos}
    return cfg


def _ok(repo):
    return runner.DownloadResult(repo, True, files=42)


def test_subdir_defaults_to_repo_name():
    assert cli._subdir("jame-louis/docker-101", config_mod.RepoSettings()) == "docker-101"


def test_subdir_uses_override():
    s = config_mod.RepoSettings(subdir="custom")
    assert cli._subdir("owner/repo", s) == "custom"


def test_sync_calls_download_for_each_repo(tmp_path, capsys):
    cfg = _repo_cfg(tmp_path, repos=("jame-louis/docker-101", "jame-louis/python-101"))
    cfg.repos["jame-louis/python-101"] = config_mod.RepoSettings(artifact="site")
    results = [
        runner.DownloadResult("jame-louis/docker-101", True, files=5),
        runner.DownloadResult("jame-louis/python-101", False, error="artifact not found"),
    ]
    with mock.patch("gh_pages_sync.runner.download", side_effect=results) as dl, \
         mock.patch("gh_pages_sync.runner.latest_success_sha", return_value=OK_SHA):
        code = cli._sync_repos(cfg)

    assert code == 1  # one repo failed
    assert dl.call_count == 2
    args0 = dl.call_args_list[0].args
    assert args0[0] == "jame-louis/docker-101"
    captured = capsys.readouterr()
    assert "docker-101" in captured.out and "python-101" in captured.out
    assert "artifact not found" in captured.err


def test_sync_skips_when_unchanged(tmp_path, capsys):
    cfg = _repo_cfg(tmp_path)
    state = cli._state_path(cfg.dest, "docker-101")
    cli._write_sha(state, OK_SHA)

    with mock.patch("gh_pages_sync.runner.download") as dl, \
         mock.patch("gh_pages_sync.runner.latest_success_sha", return_value=OK_SHA):
        code = cli._sync_repos(cfg)

    assert code == 0
    dl.assert_not_called()
    assert "unchanged" in capsys.readouterr().out


def test_sync_downloads_when_sha_changed_and_records(tmp_path, capsys):
    cfg = _repo_cfg(tmp_path)
    cli._write_sha(cli._state_path(cfg.dest, "docker-101"), "old" * 20)

    with mock.patch("gh_pages_sync.runner.download", return_value=_ok("jame-louis/docker-101")) as dl, \
         mock.patch("gh_pages_sync.runner.latest_success_sha", return_value=OK_SHA):
        code = cli._sync_repos(cfg)

    assert code == 0
    dl.assert_called_once()
    # The new sha was persisted so a follow-up run skips.
    assert cli._read_sha(cli._state_path(cfg.dest, "docker-101")) == OK_SHA


def test_sync_force_downloads_even_if_unchanged(tmp_path, capsys):
    cfg = _repo_cfg(tmp_path)
    cli._write_sha(cli._state_path(cfg.dest, "docker-101"), OK_SHA)

    with mock.patch("gh_pages_sync.runner.download", return_value=_ok("jame-louis/docker-101")) as dl, \
         mock.patch("gh_pages_sync.runner.latest_success_sha", return_value=OK_SHA):
        code = cli._sync_repos(cfg, force=True)

    assert code == 0
    dl.assert_called_once()