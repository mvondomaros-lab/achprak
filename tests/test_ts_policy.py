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
@pytest.mark.parametrize("group", ["H", "Me", "OMe", "NMe2", "CF3", "CN", "NO2"])
def test_current_menu_is_allowed_at_every_site(site, group):
    assert ts_restriction(settings((site, group))) is None


@pytest.mark.parametrize(
    "groups",
    [
        (),
        ((0, "CF3"), (5, "CF3")),
        ((2, "NMe2"), (7, "NMe2")),
        ((1, "CN"), (8, "NO2")),
    ],
)
def test_no_additional_size_or_ortho_limits(groups):
    assert ts_restriction(settings(*groups)) is None


def test_substituent_count_includes_both_rings():
    reason = ts_restriction(settings((0, "CN"), (2, "Me"), (8, "NO2")))
    assert "höchstens zwei" in reason


@pytest.mark.parametrize(
    "values",
    [
        settings((0, "CN"), (1, "NO2"), (2, "Me")),
        settings((1, "Me"), (2, "CN"), (8, "OMe")),
    ],
)
def test_api_blocks_only_ts_and_uses_stored_provenance(monkeypatch, values):
    app = create_app()
    with TestClient(app) as client:
        client.get("/api/session")
        manager = app.state.manager
        session = next(iter(manager.sessions.values()))
        session.molecules.update(
            {
                "initial": {"id": "initial", "kind": "initial", "settings": values},
                "minimum": {
                    "id": "minimum",
                    "kind": "minimum",
                    "converged": True,
                    "parent_id": "initial",
                    "settings": values,
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
        assert client.post(
            "/api/jobs",
            headers=HEADERS,
            json={"kind": "template", "settings": values},
        ).status_code == (202)
        # Direct worker calls cannot bypass the restriction, even without XYZ.
        with pytest.raises(ValueError, match="Praktikum"):
            calculate({"kind": "ts", "molecule": minimum})


def test_api_accepts_two_current_groups_without_atom_limit(monkeypatch):
    app = create_app()
    with TestClient(app) as client:
        client.get("/api/session")
        manager = app.state.manager
        session = next(iter(manager.sessions.values()))
        session.molecules["minimum"] = {
            "id": "minimum",
            "kind": "minimum",
            "converged": True,
            "settings": settings((1, "CN"), (8, "NO2")),
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
