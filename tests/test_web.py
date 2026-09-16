"""Exercise the API with real isolated chemistry workers, plus multi-session boundaries."""

import json
import os
import time
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from achprak.web.server import create_app

HEADERS = {"X-AChPrak-Request": "1"}


@pytest.fixture
def app():
    return create_app(max_jobs=2, timeout=600)


@pytest.fixture
def client(app):
    with TestClient(app) as client:
        assert client.get("/api/session").status_code == 200
        yield client


def finish(client, job_id, timeout=600):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["status"] not in {"queued", "running"}:
            assert job["status"] == "complete", job
            return job["result"]
        time.sleep(0.2)
    pytest.fail("Calculation did not finish")


def run(client, kind, **kwargs):
    response = client.post("/api/jobs", headers=HEADERS, json={"kind": kind, **kwargs})
    assert response.status_code == 202, response.text
    return finish(client, response.json()["id"])


def test_structure_properties_and_session_isolation(client):
    molecule = run(
        client,
        "template",
        settings={"configuration": "cis", "substituents": ["H"] * 10},
    )["molecule"]
    assert (
        client.post(
            "/api/jobs",
            headers=HEADERS,
            json={"kind": "ts", "molecule_id": molecule["id"]},
        ).status_code
        == 422
    )
    assert molecule["name"] == "cis-Azobenzol"
    assert molecule["atom_count"] == 24
    assert molecule["formula"] == "C12H10N2"
    assert "<svg" in molecule["svg"] and "M  END" in molecule["sdf"]
    assert all(np.isfinite(list(molecule["properties"].values())))
    definition = molecule["geometry_definition"]
    assert len(definition["dihedral_indices"]) == 4
    assert [len(ring) for ring in definition["rings"]] == [6, 6]
    assert len(definition["masses"]) == molecule["atom_count"]
    props = molecule["properties"]
    assert all(np.isfinite(list(props.values())))
    assert props["ring_distance_pm"] > 0
    assert (
        client.post(
            "/api/jobs",
            headers=HEADERS,
            json={"kind": "uvvis", "molecule_id": molecule["id"]},
        ).status_code
        == 422
    )
    cookies = dict(client.cookies)
    own_job = client.get("/api/session").json()["jobs"][0]["id"]
    client.cookies.clear()
    assert client.get("/api/session").json()["molecules"] == []
    assert client.get(f"/api/jobs/{own_job}").status_code == 404
    assert client.delete(f"/api/jobs/{own_job}", headers=HEADERS).status_code == 404
    assert (
        client.delete(f"/api/molecules/{molecule['id']}", headers=HEADERS).status_code
        == 404
    )
    client.cookies.update(cookies)
    assert client.get("/api/session").json()["molecules"][0]["properties"] == props


def test_validation_and_csrf(client):
    assert client.post("/api/jobs", json={"kind": "template"}).status_code == 403
    assert (
        client.post(
            "/api/jobs",
            headers=HEADERS,
            json={"kind": "template", "settings": {"substituents": ["bad"] * 10}},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/jobs",
            headers=HEADERS,
            json={"kind": "minimum", "molecule_id": "missing"},
        ).status_code
        == 404
    )
    assert client.get("/static/../server.py").status_code == 404
    assert "no-store" in client.get("/api/session").headers["cache-control"]
    client.cookies.clear()
    assert (
        client.post("/api/jobs", headers=HEADERS, json={"kind": "template"}).status_code
        == 401
    )


def test_cancel_and_session_job_limit(client, app):
    first = client.post("/api/jobs", headers=HEADERS, json={"kind": "template"})
    assert first.status_code == 202
    second = client.post("/api/jobs", headers=HEADERS, json={"kind": "template"})
    assert second.status_code == 409
    job_id = first.json()["id"]
    assert (
        client.delete(f"/api/jobs/{job_id}", headers=HEADERS).json()["status"]
        == "cancelled"
    )
    assert job_id not in app.state.manager.tasks
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "cancelled"


def test_timeout_kills_worker():
    app = create_app(timeout=0.01)
    with TestClient(app) as client:
        client.get("/api/session")
        job_id = client.post(
            "/api/jobs", headers=HEADERS, json={"kind": "template"}
        ).json()["id"]
        for _ in range(40):
            job = client.get(f"/api/jobs/{job_id}").json()
            if job["status"] == "timeout":
                break
            time.sleep(0.1)
        assert job["status"] == "timeout"
        assert job_id not in app.state.manager.tasks
    assert not app.state.manager.root.exists()


def test_only_predefined_structure_inputs_are_accepted(client):
    for payload in [
        {"kind": "import", "xyz": "24\n..."},
        {"kind": "template", "name": "Custom name"},
        {"kind": "template", "xyz": "24\n..."},
    ]:
        response = client.post("/api/jobs", headers=HEADERS, json=payload)
        assert response.status_code == 422
    assert client.get("/api/session").json()["jobs"] == []
    assert client.get("/health").json() == {"status": "ok"}


def test_template_names_follow_configuration_and_substituents(client):
    m = run(
        client,
        "template",
        settings={
            "configuration": "cis",
            "substituents": ["NO2", "H", "Me"] + ["H"] * 6 + ["OMe"],
        },
    )["molecule"]
    assert m["name"] == "cis-2-NO2, 4-Me, 6′-OMe-Azobenzol"
    assert m["base_name"] == m["name"]
    assert m["kind"] == "initial"


@pytest.mark.skipif(
    os.environ.get("ACHPRAK_CHEMISTRY_TESTS") != "1",
    reason="Opt-in full scientific stack smoke test",
)
def test_minimum_spectrum_and_transition_state(client):
    initial = run(client, "template")["molecule"]
    minimum = run(client, "minimum", molecule_id=initial["id"])["molecule"]
    assert minimum["converged"] and minimum["kind"] == "minimum"
    assert len(minimum["frames"]) > 1
    assert all(len(frame) == minimum["atom_count"] * 3 for frame in minimum["frames"])
    assert np.isfinite(np.array(minimum["frames"])).all()
    spec = run(client, "uvvis", molecule_id=minimum["id"])["spectrum"]
    assert len(spec["energy_ev"]) == len(spec["absorption"]) == 1000
    assert max(spec["absorption"]) > 0 and len(spec["excitations_ev"]) > 0
    assert "<svg" in spec["svg"]
    ts = run(client, "ts", molecule_id=minimum["id"])["molecule"]
    assert ts["converged"] and ts["kind"] == "ts"
    assert ts["name"] == initial["name"] + " · Übergangszustand"
    ts_job = client.get("/api/session").json()["jobs"][-1]
    output_log = client.get(f"/api/jobs/{ts_job['id']}").json()["log"]
    from achprak.web.worker import PROGRESS_PREFIX

    progress = [
        json.loads(line.removeprefix(PROGRESS_PREFIX))
        for line in output_log.splitlines()
        if line.startswith(PROGRESS_PREFIX)
    ]
    assert progress and progress[-1]["phase"] == "complete"
    # Earlier phases may have left the bounded live log; check the full history below.
    assert progress[-1]["source_id"] == minimum["id"]
    assert len(ts["frames"]) == len(ts["optimization_history"])
    np.testing.assert_allclose(
        ts["frames"], [p["positions"] for p in ts["optimization_history"]], atol=1e-6
    )
    assert ts["ts_search"]["validation"]["verified"]
    assert ts["ts_search"]["validation"]["imaginary_count"] == 1
    assert (
        len(ts["ts_search"]["validation"]["frequencies_cm1"])
        == 3 * ts["atom_count"] - 6
    )
    assert ts["ts_search"]["barrier_ev"] > 0
    history = ts["optimization_history"]
    assert history[0]["step"] == 0
    assert history[0]["phase"] == "endpoint"
    np.testing.assert_allclose(
        history[0]["positions"], minimum["frames"][-1], atol=1e-6
    )
    assert history[-1]["phase"] == "complete"
    assert history[-1]["energy_ev"] > history[0]["energy_ev"]
    assert ts["ts_search"]["barrier_ev"] == pytest.approx(
        history[-1]["energy_ev"] - history[0]["energy_ev"]
    )
    assert {p["phase"] for p in history} >= {
        "path_seed",
        "neb",
        "neb_climb",
        "refinement",
        "vibrations",
        "connectivity",
        "complete",
    }
    assert len({p["step"] for p in history}) > 1
    assert all(len(p["positions"]) == ts["atom_count"] * 3 for p in history)
    assert np.isfinite(np.array(ts["frames"])).all()
    assert np.ptp(np.array(ts["frames"]), axis=0).max() > 0.01
    output = Path(os.environ.get("ACHPRAK_TEST_OUTPUT", "/tmp/achprak-web-smoke.json"))
    output.write_text(
        json.dumps({"initial": initial, "minimum": minimum, "spectrum": spec, "ts": ts})
    )


def test_live_optimization_records(client):
    from achprak.web.worker import PROGRESS_PREFIX

    initial = run(client, "template")["molecule"]
    response = client.post(
        "/api/jobs",
        headers=HEADERS,
        json={"kind": "minimum", "molecule_id": initial["id"]},
    )
    job_id = response.json()["id"]
    minimum = finish(client, job_id)["molecule"]
    assert minimum["settings"] == initial["settings"]
    rejected = client.post(
        "/api/jobs",
        headers=HEADERS,
        json={"kind": "minimum", "molecule_id": minimum["id"]},
    )
    assert rejected.status_code == 422
    saved = next(
        m
        for m in client.get("/api/session").json()["molecules"]
        if m["id"] == minimum["id"]
    )
    assert saved["optimization_history"] == minimum["optimization_history"]
    job = client.get(f"/api/jobs/{job_id}").json()
    records = [
        json.loads(line.removeprefix(PROGRESS_PREFIX))
        for line in job["log"].splitlines()
        if line.startswith(PROGRESS_PREFIX)
    ]
    assert len(records) >= 2
    assert all(record["source_id"] == initial["id"] for record in records)
    assert all(
        len(record["positions"]) == initial["atom_count"] * 3 for record in records
    )
    assert records[-1]["step"] > records[0]["step"]
    assert records[-1]["fmax_ev_angstrom"] < 0.02
    assert np.isfinite(records[-1]["energy_ev"])
    history = minimum["optimization_history"]
    assert history[0]["step"] == 0
    assert [p["step"] for p in history] == list(range(len(history)))
    assert len(history) == len(minimum["frames"])
    assert history[-1] == records[-1]
    # Full history survives independently of the bounded live log and remains
    # available when selecting an older result or reloading the page.
    saved = next(
        m
        for m in client.get("/api/session").json()["molecules"]
        if m["id"] == minimum["id"]
    )
    assert saved["optimization_history"] == history
    np.testing.assert_allclose(
        records[-1]["positions"], minimum["frames"][-1], atol=1e-6
    )
    assert minimum["base_name"] == initial["name"]
    assert minimum["name"] == initial["name"] + " · Minimum"


@pytest.mark.skipif(
    os.environ.get("ACHPRAK_CHEMISTRY_TESTS") != "1"
    and os.environ.get("ACHPRAK_TS_TESTS") != "1",
    reason="Opt-in minimum-to-TS path checks",
)
@pytest.mark.ts_optimization
@pytest.mark.parametrize(
    "configuration,substituents",
    [
        pytest.param("trans", ["H"] * 10, id="trans-H"),
        pytest.param("cis", ["H"] * 10, id="cis-H"),
        pytest.param("trans", ["Me"] + ["H"] * 9, id="trans-2-Me"),
        pytest.param("cis", ["Me"] + ["H"] * 9, id="cis-2-Me"),
        pytest.param("trans", ["CN"] + ["H"] * 9, id="trans-2-CN"),
        pytest.param("cis", ["NO2"] + ["H"] * 9, id="cis-2-NO2"),
        pytest.param("trans", ["NMe2"] + ["H"] * 9, id="trans-2-NMe2"),
        pytest.param(
            "trans",
            ["H", "H", "NMe2", "H", "H", "H", "H", "CF3", "H", "H"],
            id="trans-4-NMe2-4prime-CF3",
        ),
    ],
)
def test_ts_paths_from_cis_and_substituted_minima(
    client, configuration, substituents, tmp_path
):
    initial = run(
        client,
        "template",
        settings={"configuration": configuration, "substituents": substituents},
    )["molecule"]
    minimum = run(client, "minimum", molecule_id=initial["id"])["molecule"]
    assert minimum["converged"]
    assert minimum["optimization_history"][-1]["fmax_ev_angstrom"] <= 0.002
    ts = run(client, "ts", molecule_id=minimum["id"])["molecule"]
    report = tmp_path / "ts-result.json"
    report.write_text(json.dumps({"initial": initial, "minimum": minimum, "ts": ts}))
    assert ts["converged"], (
        f"{ts.get('ts_search', {}).get('failure_reason')}; diagnostics: {report}"
    )
    search = ts["ts_search"]
    assert search["max_attempts"] == 2
    assert len(search["attempts"]) <= 2
    assert search["source_minimum_id"] == minimum["id"]
    assert search["validation"]["verified"]
    assert search["validation"]["imaginary_count"] == 1
    frequencies = np.array(search["validation"]["frequencies_cm1"])
    assert len(frequencies) == 3 * initial["atom_count"] - 6
    assert np.isfinite(frequencies).all()
    assert np.count_nonzero(frequencies < -20.0) == 1
    assert search["barrier_ev"] > 0
    assert all(a["iterations"] <= 1500 for a in search["attempts"])
    assert search["iterations"] == sum(a["iterations"] for a in search["attempts"])
    assert search["method"] == "ci_neb_then_sella"
    assert search["band_converged"]
    if configuration == "cis" and set(substituents) == {"H"}:
        assert search["connectivity"]["endpoint_conformers_match"]
    assert search["connectivity"]["verified"]
    assert search["connectivity"]["minimum_fmax_ev_angstrom"] == 0.002
    assert {b["isomer"] for b in search["connectivity"]["branches"]} == {"cis", "trans"}
    assert all(
        b["converged"] and b["bonds_preserved"] and b["xyz"]
        for b in search["connectivity"]["branches"]
    )
    path = search["path"]
    assert len(path) == 13
    assert path[0]["coordinate"] == 0 and path[-1]["coordinate"] == 1
    assert all(b["coordinate"] > a["coordinate"] for a, b in zip(path, path[1:]))
    assert search["other_minimum"]["xyz"]
    assert max(p["energy_ev"] for p in path) > max(
        path[0]["energy_ev"], path[-1]["energy_ev"]
    )
    assert search["barrier_ev"] == pytest.approx(
        max(p["energy_ev"] for p in path) - path[0]["energy_ev"], abs=0.02
    )
    history = ts["optimization_history"]
    np.testing.assert_allclose(
        history[0]["positions"], minimum["frames"][-1], atol=1e-6
    )
    assert history[0]["phase"] == "endpoint"
    neb_records = [p for p in history if p["phase"] == "neb"]
    assert {p["neb_image"] for p in neb_records} == {3, 9}
    for image_index in (3, 9):
        snapshots = [p for p in neb_records if p["neb_image"] == image_index]
        assert (
            np.max(
                np.abs(np.array(snapshots[-1]["positions"]) - snapshots[0]["positions"])
            )
            > 0.01
        )
    for p in neb_records:
        assert p["energy_ev"] == pytest.approx(
            p["neb_path"][p["neb_image"]]["energy_ev"]
        )
    assert history[-1]["fmax_ev_angstrom"] <= 0.005
    assert len(ts["frames"]) == len(ts["optimization_history"])
    np.testing.assert_allclose(
        ts["frames"], [p["positions"] for p in ts["optimization_history"]], atol=1e-6
    )


@pytest.mark.parametrize("kind", ["minimum", "ts"])
@pytest.mark.parametrize("ok", [True, False])
def test_repeated_search_replaces_only_its_previous_result(kind, ok):
    from achprak.web.server import JobManager, Session

    manager = JobManager()
    source = {"id": "start", "kind": "initial", "base_name": "cis-Azobenzol"}
    previous = {
        "id": "old",
        "kind": kind,
        "base_name": "cis-Azobenzol",
        "optimization_history": [1, 2, 3],
    }
    unrelated = {"id": "other", "kind": kind, "base_name": "trans-Azobenzol"}
    session = Session(molecules={m["id"]: m for m in [source, previous, unrelated]})

    class Finished:
        returncode = 0

        def poll(self):
            return 0

    try:
        job = manager.submit(session, {"kind": kind, "molecule": source})
        folder = manager.root / job["id"]
        result = {
            "id": "new",
            "kind": kind,
            "base_name": "cis-Azobenzol",
            "optimization_history": [4, 5],
        }
        (folder / "result.json").write_text(
            json.dumps(
                {"ok": ok, "result": {"molecule": result}, "error": "Search failed"}
            )
        )
        job.update(started=time.monotonic(), status="running")
        manager.tasks[job["id"]] = (session, job, folder, Finished())
        assert session.molecules["old"] == previous
        manager.tick()
        assert session.molecules["start"] == source
        assert session.molecules["other"] == unrelated
        if ok:
            assert "old" not in session.molecules
            assert session.molecules["new"]["optimization_history"] == [4, 5]
        else:
            assert session.molecules["old"] == previous
            assert "new" not in session.molecules
    finally:
        manager.close()


def test_clear_structures_is_session_scoped_and_blocked_during_jobs(client, app):
    session = next(iter(app.state.manager.sessions.values()))
    session.molecules.update(
        {kind: {"id": kind, "kind": kind} for kind in ("initial", "minimum", "ts")}
    )
    cookies = dict(client.cookies)
    client.cookies.clear()
    client.get("/api/session")
    other = next(s for s in app.state.manager.sessions.values() if s is not session)
    other.molecules["other"] = {"id": "other", "kind": "initial"}
    client.cookies.clear()
    client.cookies.update(cookies)
    assert client.delete("/api/molecules").status_code == 403
    for status in ("queued", "running"):
        session.jobs["active"] = {"status": status}
        assert client.delete("/api/molecules", headers=HEADERS).status_code == 409
        assert len(session.molecules) == 3
    session.jobs.clear()
    assert client.delete("/api/molecules", headers=HEADERS).status_code == 200
    assert client.get("/api/session").json()["molecules"] == []
    assert list(other.molecules) == ["other"]
    assert client.delete("/api/molecules", headers=HEADERS).status_code == 200


def test_spectrum_progress_survives_log_truncation_and_is_session_scoped(
    client, app, monkeypatch
):
    from achprak.web.worker import spectrum_progress

    session = next(iter(app.state.manager.sessions.values()))
    session.jobs["spectrum"] = {"id": "spectrum", "kind": "uvvis", "status": "running"}
    folder = app.state.manager.root / "spectrum"
    folder.mkdir()
    monkeypatch.chdir(folder)
    assert client.get("/api/jobs/spectrum").json()["spectrum_progress"] is None
    spectrum_progress("excited_states")
    (folder / "output.log").write_text("unrelated output\n" * 3000)
    result = client.get("/api/jobs/spectrum").json()
    assert result["spectrum_progress"] == {"phase": "excited_states"}
    assert len(result["log"]) == 24000
    spectrum_progress("plot")
    assert client.get("/api/jobs/spectrum").json()["spectrum_progress"] == {
        "phase": "plot"
    }
    assert not (folder / "spectrum-progress.tmp").exists()
    client.cookies.clear()
    client.get("/api/session")
    assert client.get("/api/jobs/spectrum").status_code == 404


def test_existing_spectrum_is_preserved_and_missing_spectrum_can_be_requested(
    client, app, monkeypatch
):
    manager = app.state.manager
    session = next(iter(manager.sessions.values()))
    spectrum = {"energy_ev": [2.0], "absorption": [1.0]}
    molecule = {"id": "minimum", "kind": "minimum", "spectrum": spectrum}
    session.molecules["minimum"] = molecule
    submissions = []

    def submit(session, payload):
        submissions.append(payload)
        return {"kind": payload["kind"], "status": "queued"}

    monkeypatch.setattr(manager, "submit", submit)
    request = {"kind": "uvvis", "molecule_id": "minimum"}
    response = client.post("/api/jobs", headers=HEADERS, json=request)
    assert response.status_code == 422
    assert "bereits ein Spektrum" in response.json()["detail"]
    assert submissions == []
    assert molecule["spectrum"] == spectrum
    del molecule["spectrum"]
    assert client.post("/api/jobs", headers=HEADERS, json=request).status_code == 202
    assert len(submissions) == 1


def test_minimization_of_transition_state_is_rejected(client, app):
    from achprak.web.worker import calculate

    session = next(iter(app.state.manager.sessions.values()))
    ts = {"id": "ts-result", "kind": "ts", "converged": True}
    session.molecules[ts["id"]] = ts
    response = client.post(
        "/api/jobs",
        headers=HEADERS,
        json={"kind": "minimum", "molecule_id": ts["id"]},
    )
    assert response.status_code == 422
    assert "Wählen Sie eine Startstruktur" in response.json()["detail"]
    assert not session.jobs
    assert session.molecules[ts["id"]] == ts
    with pytest.raises(ValueError, match="Wählen Sie eine Startstruktur"):
        calculate({"kind": "minimum", "molecule": ts})


@pytest.mark.parametrize(
    "hub_env, expected",
    [
        ({}, None),
        (
            {"JUPYTERHUB_USER": "student", "JUPYTERHUB_BASE_URL": "/"},
            {"home": "/hub/home", "logout": "/hub/logout"},
        ),
        (
            {"JUPYTERHUB_USER": "student", "JUPYTERHUB_BASE_URL": "/jhub/"},
            {"home": "/jhub/hub/home", "logout": "/jhub/hub/logout"},
        ),
        (
            {
                "JUPYTERHUB_USER": "student",
                "JUPYTERHUB_BASE_URL": "/course/",
                "JUPYTERHUB_HOST": "https://hub.example.org",
            },
            {
                "home": "https://hub.example.org/course/hub/home",
                "logout": "https://hub.example.org/course/hub/logout",
            },
        ),
        (
            {
                "JUPYTERHUB_USER": "student",
                "JUPYTERHUB_PUBLIC_HUB_URL": "https://hub.example.org/course/hub/",
                "JUPYTERHUB_BASE_URL": "/ignored/",
                "JUPYTERHUB_API_URL": "http://private-hub:8081/hub/api",
            },
            {
                "home": "https://hub.example.org/course/hub/home",
                "logout": "https://hub.example.org/course/hub/logout",
            },
        ),
    ],
)
def test_session_hub_navigation(client, monkeypatch, hub_env, expected):
    for key in (
        "JUPYTERHUB_USER",
        "JUPYTERHUB_BASE_URL",
        "JUPYTERHUB_HOST",
        "JUPYTERHUB_PUBLIC_HUB_URL",
        "JUPYTERHUB_API_URL",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in hub_env.items():
        monkeypatch.setenv(key, value)
    assert client.get("/api/session").json()["hub"] == expected
