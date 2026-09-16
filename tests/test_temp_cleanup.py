"""Scratch ownership and cleanup, including workers killed without Python cleanup."""

import json
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import pytest
from ase import Atoms

from achprak import uvvis
from achprak.web.server import JobManager, Session


@pytest.fixture
def manager():
    manager = JobManager()
    yield manager
    manager.close()
    assert not manager.root.exists()


@pytest.mark.parametrize("result", ["success", "failure", "invalid", "missing"])
def test_finished_job_removes_files_and_preserves_output(manager, result):
    session = Session()
    job = manager.submit(session, {"kind": "uvvis"})
    folder = manager.root / job["id"]
    molecule = {"id": "m", "kind": "initial"}
    if result in {"success", "failure"}:
        (folder / "result.json").write_text(
            json.dumps(
                {
                    "ok": result == "success",
                    "result": {"molecule": molecule},
                    "error": "calculation failed",
                }
            )
        )
    elif result == "invalid":
        (folder / "result.json").write_text("{")
    (folder / "output.log").write_text("x" * 30000 + "last line\n")
    (folder / "spectrum-progress.json").write_text('{"phase": "plot"}')
    scratch = folder / "scratch"
    scratch.mkdir()
    (scratch / "large.out").write_text("scratch output")

    class Finished:
        returncode = 0

        def poll(self):
            return 0

    job.update(status="running", started=time.monotonic())
    manager.tasks[job["id"]] = (session, job, folder, Finished())
    manager.tick()
    assert job["status"] == ("complete" if result == "success" else "failed")
    assert not folder.exists()
    assert len(job["log"]) == 24000
    assert job["log"].endswith("last line\n")
    assert job["spectrum_progress"] == {"phase": "plot"}
    if result == "success":
        assert session.molecules["m"] == molecule


def test_queued_cancellation_and_submission_failure(manager):
    session = Session()
    with pytest.raises(TypeError):
        manager.submit(session, {"kind": "template", "invalid": object()})
    assert not list(manager.root.iterdir())
    assert not session.jobs
    job = manager.submit(session, {"kind": "template"})
    manager.stop(job["id"])
    manager.stop(job["id"])  # Cancellation remains idempotent.
    assert job["status"] == "cancelled"
    assert not list(manager.root.iterdir())


def test_process_start_failure(manager, monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("cannot start worker")

    monkeypatch.setattr(subprocess, "Popen", fail)
    job = manager.submit(Session(), {"kind": "template"})
    manager.tick()
    assert job["status"] == "failed"
    assert not manager.tasks
    assert not list(manager.root.iterdir())


@pytest.mark.parametrize("reason", ["cancel", "timeout", "expiry", "shutdown"])
def test_killed_worker_scratch_is_owned_by_parent(manager, monkeypatch, reason):
    real_popen = subprocess.Popen
    script = """
import json, tempfile, time
from pathlib import Path
with tempfile.NamedTemporaryFile(suffix='.traj') as trajectory:
    with tempfile.TemporaryDirectory() as scratch:
        Path(scratch, 'vibration.json').write_text('scratch')
        Path('ready.json').write_text(json.dumps([trajectory.name, scratch]))
        time.sleep(60)
"""

    def start_worker(command, **kwargs):
        return real_popen([sys.executable, "-c", script], **kwargs)

    monkeypatch.setattr(subprocess, "Popen", start_worker)
    session = Session()
    manager.sessions["session"] = session
    job = manager.submit(session, {"kind": "minimum"})
    folder = manager.root / job["id"]
    manager.tick()
    proc = manager.tasks[job["id"]][3]
    deadline = time.monotonic() + 10
    while not (folder / "ready.json").exists():
        assert proc.poll() is None
        assert time.monotonic() < deadline
        time.sleep(0.02)
    scratch_paths = json.loads((folder / "ready.json").read_text())
    assert all(Path(path).is_relative_to(folder) for path in scratch_paths)
    assert all(Path(path).exists() for path in scratch_paths)
    if reason == "cancel":
        manager.stop(job["id"])
    elif reason == "timeout":
        job["started"] -= manager.timeout + 1
        manager.tick()
        assert job["status"] == "timeout"
    elif reason == "expiry":
        session.touched -= manager.session_ttl + 1
        manager.tick()
        assert not manager.sessions
    else:
        manager.close()
    assert proc.poll() is not None
    assert not folder.exists()
    assert all(not Path(path).exists() for path in scratch_paths)


@pytest.mark.parametrize("failure", [None, "input", "run", "parse"])
def test_mopac_files_are_cleaned_even_on_failure(monkeypatch, failure):
    # Use the actual wrapper's directory creation, without running chemistry.
    original_input = uvvis.pymopac.MopacInput
    paths = []

    def make_input(*args, **kwargs):
        mopac = original_input(*args, **kwargs)
        path = Path(mopac.path)
        paths.append(path)
        (path / "scratch.out").write_text("output")
        if failure == "input":
            raise RuntimeError("input")

        def run():
            if failure == "run":
                raise RuntimeError("run")
            mopac.outpath = path / "scratch.out"

        mopac.run = run
        return mopac

    def parse(path):
        assert path.exists()
        if failure == "parse":
            raise RuntimeError("parse")
        return np.linspace(2, 5 if len(paths) == 1 else 8, 99), np.ones(99)

    monkeypatch.setattr(uvvis.pymopac, "MopacInput", make_input)
    monkeypatch.setattr(uvvis, "parse_mopac_excitations", parse)
    spec = uvvis.UVVis(Atoms("H2", positions=[[0, 0, 0], [0, 0, 0.74]]))
    assert paths == []  # Merely constructing a spectrum creates no files.
    if failure:
        with pytest.raises(RuntimeError, match=failure):
            spec.calculate()
    else:
        spec.calculate()
        assert len(paths) == 2
        assert paths[0] != paths[1]
        assert spec.coverage_complete
    assert paths
    assert all(not path.parent.exists() for path in paths)
