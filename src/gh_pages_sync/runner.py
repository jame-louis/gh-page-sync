"""Download a repo's GitHub Actions build output into a local dir via ``gh``.

``gh run download -n <artifact>`` fetches the latest successful run's Pages
deployment artifact. For a genuine ``upload-artifact`` it is unzipped by ``gh``
into ``--dir/<name>/``; for a Pages deployment it is delivered as a single
``artifact.tar``. :func:`_flatten` normalises both so the site files land
directly at ``<dest>/<repo>/index.html``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tarfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DownloadResult:
    repo: str
    ok: bool
    files: int = 0
    outdir: Path | None = None
    error: str | None = None


def _find_gh() -> str | None:
    """Locate the ``gh`` CLI.

    When frozen (PyInstaller), prefer a ``gh.exe`` sitting next to the
    executable so the tool can ship fully self-contained; otherwise fall back
    to ``gh`` on PATH.
    """
    if getattr(sys, "frozen", False):
        local = Path(sys.executable).with_name("gh.exe")
        if local.is_file():
            return str(local)
    return shutil.which("gh")


def build_cmd(repo: str, artifact: str, outdir: Path, run_id: str | int | None = None) -> list[str]:
    """Assemble the ``gh run download`` argv (pure, unit-testable)."""
    argv = ["gh", "run", "download"]
    if run_id is not None:
        argv.append(str(run_id))
    argv += ["--repo", repo, "--name", artifact, "--dir", str(outdir)]
    return argv


def _flatten(outdir: Path) -> None:
    """Normalise ``outdir`` so site files land directly under it.

    Two shapes show up depending on the artifact type:

    - A normal ``upload-artifact`` is unzipped by ``gh`` into a folder named
      after the artifact: ``X/name/...``. If ``outdir`` holds exactly one
      directory and no loose files, move its contents up.
    - A Pages deployment artifact is delivered as a single ``artifact.tar``. If
      ``outdir`` holds exactly one ``.tar`` and nothing else, extract it in
      place and delete the tarball.
    """
    children = [p for p in outdir.iterdir()]
    dirs = [p for p in children if p.is_dir()]
    loose = [p for p in children if p.is_file()]
    if len(dirs) == 1 and not loose:
        art = dirs[0]
        for item in art.iterdir():
            shutil.move(str(item), str(outdir / item.name))
        art.rmdir()
        return
    tars = [p for p in loose if p.suffix == ".tar"]
    if len(tars) == 1 and len(loose) == 1 and not dirs:
        tarball = tars[0]
        with tarfile.open(tarball) as tf:
            tf.extractall(outdir, filter="data")
        tarball.unlink()


def _count_files(root: Path) -> int:
    return sum(1 for p in root.rglob("*") if p.is_file())


def download(
    repo: str,
    artifact: str,
    outdir: Path,
    *,
    run_id: str | int | None = None,
) -> DownloadResult:
    """Run ``gh run download`` for ``repo`` into ``outdir``; flatten + count."""
    gh = _find_gh()
    if gh is None:
        return DownloadResult(
            repo, False,
            error="'gh' not found on PATH (install: 'brew install gh' then 'gh auth login')",
        )
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    proc = subprocess.run(
        build_cmd(repo, artifact, outdir, run_id),
        capture_output=True,
        text=True,
    )
    err = proc.stderr.strip()
    if proc.returncode != 0:
        detail = err or f"gh run download exited with status {proc.returncode}"
        return DownloadResult(repo, False, error=detail)

    _flatten(outdir)
    return DownloadResult(repo, True, files=_count_files(outdir), outdir=outdir)