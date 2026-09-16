"""Course TS limits are enforced before launching a worker, without restricting other jobs."""

import pytest
from fastapi.testclient import TestClient

from achprak.web.server import create_app
from achprak.web.ts_policy import ts_restriction
from achprak.web.worker import calculate

HEADERS = {"X-AChPrak-Request": "1"}


def settings(*pairs):
    values = ["H"] * 10
    for index, group in pairs:
        values[index] = group
    return {"configuration": "trans", "substituents": values}


@pytest.mark.parametrize("site", range(10))
def test_only_ortho_so2cf3_is_excluded(site):
    reason = ts_restriction(settings((site, "SO2CF3")))
    assert bool(reason) == (site in {0, 4, 5, 9})


@pytest.mark.parametrize(
    "groups",
    [
        (),
        ((0, "CF3"), (5, "CF3")),
        ((2, "NMe2"), (7, "NMe2")),
        ((1, "SO2CF3"), (8, "SO2CF3")),
    ],
)
def test_no_additional_size_or_ortho_limits(groups):
    assert ts_restriction(settings(*groups)) is None


def test_substituent_count_includes_both_rings_and_reports_both_restrictions():
    reason = ts_restriction(settings((0, "SO2CF3"), (2, "Me"), (8, "F")))
    assert "höchstens zwei" in reason
    assert "ortho" in reason


@pytest.mark.parametrize(
    "values", [settings((0, "SO2CF3")), settings((1, "Me"), (2, "F"), (8, "OMe"))]
)
def test_api_blocks_only_ts_and_uses_stored_provenance(monkeypatch, values):
    app = create_app()
    with TestClient(app) as client:
        client.get("/api/session")
        manager = app.state.manager
        session = next(iter(manager.sessions.values()))
        # An old minimum may have settings only on its parent structure.
        session.molecules.update(
            {
                "initial": {"id": "initial", "kind": "initial", "settings": values},
                "minimum": {
                    "id": "minimum",
                    "kind": "minimum",
                    "converged": True,
                    "parent_id": "initial",
                },
            }
        )
        submitted = []

        def submit(session, payload):
            submitted.append(payload)
            return {"id": "test-job", "status": "queued"}

        monkeypatch.setattr(manager, "submit", submit)
        molecules = client.get("/api/session").json()["molecules"]
        minimum = next(m for m in molecules if m["id"] == "minimum")
        assert minimum["settings"] == values
        assert minimum["ts_restriction"]
        response = client.post(
            "/api/jobs",
            headers=HEADERS,
            json={
                "kind": "ts",
                "molecule_id": "minimum",
                "settings": settings(),
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"] == minimum["ts_restriction"]
        assert not submitted
        for kind, source in (("minimum", "initial"), ("uvvis", "minimum")):
            response = client.post(
                "/api/jobs", headers=HEADERS, json={"kind": kind, "molecule_id": source}
            )
            assert response.status_code == 202
            assert submitted[-1]["molecule"]["settings"] == values
        assert (
            client.post(
                "/api/jobs",
                headers=HEADERS,
                json={"kind": "template", "settings": values},
            ).status_code
            == (422 if any(v in {"F", "SO2CF3"} for v in values["substituents"]) else 202)
        )
        # Direct worker calls cannot bypass the restriction, even without XYZ.
        with pytest.raises(ValueError, match="Praktikum"):
            calculate({"kind": "ts", "molecule": minimum})


def test_api_accepts_two_nonortho_so2cf3_without_atom_limit(monkeypatch):
    app = create_app()
    with TestClient(app) as client:
        client.get("/api/session")
        manager = app.state.manager
        session = next(iter(manager.sessions.values()))
        session.molecules["minimum"] = {
            "id": "minimum",
            "kind": "minimum",
            "converged": True,
            "settings": settings((1, "SO2CF3"), (8, "SO2CF3")),
            "atom_count": 100,
        }
        monkeypatch.setattr(
            manager, "submit", lambda session, payload: {"id": "test-job"}
        )
        assert (
            client.post(
                "/api/jobs",
                headers=HEADERS,
                json={"kind": "ts", "molecule_id": "minimum"},
            ).status_code
            == 202
        )


def test_unknown_provenance_does_not_silently_bypass_ts_limits():
    assert ts_restriction(None)
    with pytest.raises(ValueError, match="nicht mehr zugeordnet"):
        calculate({"kind": "ts", "molecule": {"kind": "minimum", "converged": True}})
