"""Binder must use the installed app and exclude local build artifacts."""

import os
from pathlib import Path
import runpy
from types import SimpleNamespace

from docker.utils.build import exclude_paths
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_local_build_context_excludes_environments_and_results(tmp_path):
    required = {
        "pyproject.toml",
        "pixi.lock",
        "binder/postBuild",
        "binder/start",
        "src/photoswitchlab/web/static/index.html",
    }
    excluded = {
        ".pixi/envs/web/bin/python",
        ".venv/bin/python",
        ".git/config",
        "results/run.json",
        "site/_build/index.html",
        "src/photoswitchlab/__pycache__/server.pyc",
        "src/photoswitchlab.egg-info/PKG-INFO",
    }
    for name in required | excluded:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    patterns = [
        line
        for line in (ROOT / "binder/.dockerignore").read_text().splitlines()
        if line and not line.startswith("#")
    ]
    context = exclude_paths(str(tmp_path), patterns)
    assert required <= context
    assert not excluded & context


@pytest.mark.parametrize("secure", [False, True])
def test_binder_proxy_launch_does_not_need_build_tools(tmp_path, monkeypatch, secure):
    monkeypatch.setenv("PHOTOSWITCHLAB_BINDER_ROOT", str(tmp_path))
    monkeypatch.delenv("JUPYTERHUB_SERVICE_PREFIX", raising=False)
    if secure:
        monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/binder-test/")
    config = SimpleNamespace(ServerProxy=SimpleNamespace())
    runpy.run_path(
        str(ROOT / "binder/jupyter_server_config.py"),
        init_globals={"get_config": lambda: config},
    )
    server = config.ServerProxy.servers["photoswitchlab"]
    command = server["command"]("/tmp/app.sock", "/user/binder-test/")
    assert command[:3] == [
        str(tmp_path / ".pixi/envs/web/bin/python"),
        "-m",
        "photoswitchlab.web",
    ]
    assert "--cookie-path=/user/binder-test/photoswitchlab/" in command
    assert ("--secure-cookie" in command) == secure
    environment = server["environment"]
    assert environment["PATH"].split(os.pathsep)[0] == str(
        tmp_path / ".pixi/envs/web/bin"
    )
    assert environment["PYTHONNOUSERSITE"] == "1"
    assert environment["OMP_NUM_THREADS"] == "1"
