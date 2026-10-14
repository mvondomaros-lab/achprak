"""Deployment regression: personal Python packages must not shadow app packages."""

import os
from pathlib import Path
import runpy
import subprocess
import sys
import pytest
from types import SimpleNamespace


@pytest.mark.parametrize("legacy", [False, True])
def test_hub_environment_and_course_settings_support_existing_deployments(
    tmp_path, monkeypatch, legacy
):
    monkeypatch.delenv("PHOTOSWITCHLAB_ENV", raising=False)
    monkeypatch.delenv("PHOTOSWITCHLAB_COURSE", raising=False)
    monkeypatch.setenv("ACHPRAK_ENV", str(tmp_path / "legacy"))
    monkeypatch.setenv("ACHPRAK_COURSE", "marburg")
    chosen = tmp_path / "legacy"
    if not legacy:
        chosen = tmp_path / "current"
        monkeypatch.setenv("PHOTOSWITCHLAB_ENV", str(chosen))
        monkeypatch.setenv("PHOTOSWITCHLAB_COURSE", "public")
    config = SimpleNamespace(
        Spawner=SimpleNamespace(environment={"OTHER_SETTING": "retained"})
    )
    fragment = Path(__file__).resolve().parents[1] / "deploy/jupyterhub_integration.py"
    runpy.run_path(str(fragment), init_globals={"get_config": lambda: config})
    assert config.Spawner.cmd == [str(chosen / "bin/jupyter-standaloneproxy")]
    assert str(chosen / "bin/python") in config.Spawner.args
    assert "photoswitchlab.web" in config.Spawner.args
    assert config.Spawner.environment["PHOTOSWITCHLAB_COURSE"] == (
        "marburg" if legacy else "public"
    )
    assert config.Spawner.environment["OTHER_SETTING"] == "retained"


def test_personal_packages_are_excluded_from_spawned_python(tmp_path):
    config = SimpleNamespace(Spawner=SimpleNamespace(environment={}))
    fragment = Path(__file__).resolve().parents[1] / "deploy/jupyterhub_integration.py"
    runpy.run_path(str(fragment), init_globals={"get_config": lambda: config})

    env = {**os.environ, "PYTHONUSERBASE": str(tmp_path)}
    env.pop("PYTHONNOUSERSITE", None)
    user_site = Path(
        subprocess.check_output(
            [sys.executable, "-c", "import site; print(site.getusersitepackages())"],
            env=env,
            text=True,
        ).strip()
    )
    user_site.mkdir(parents=True)
    (user_site / "typing_extensions.py").write_text(
        'raise RuntimeError("personal typing_extensions loaded")\n'
    )
    probe = [sys.executable, "-c", "import typing_extensions"]
    unprotected = subprocess.run(probe, env=env, capture_output=True, text=True)
    assert "personal typing_extensions loaded" in unprotected.stderr

    env.update(config.Spawner.environment)
    protected = subprocess.run(probe, env=env, capture_output=True, text=True)
    assert protected.returncode == 0, protected.stderr
    # Workers start a fresh interpreter and must inherit the same protection.
    worker = subprocess.run(
        [
            sys.executable,
            "-c",
            "import subprocess, sys; "
            "subprocess.run([sys.executable, '-c', 'import typing_extensions'], check=True)",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert worker.returncode == 0, worker.stderr
