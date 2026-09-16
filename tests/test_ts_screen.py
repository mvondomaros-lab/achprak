"""Saved failures from the exhaustive template screen; real chemistry is opt-in."""

import json
import os
from pathlib import Path

import numpy as np
import pytest

from achprak import azobenzene, common, optimization
from achprak.transition_state import OptTS
from achprak.web.ts_policy import MAX_TS_ATTEMPTS, ts_restriction

FAILURES = sorted((Path(__file__).parent / "data/ts_failures").glob("*.json"))


@pytest.mark.ts_optimization
@pytest.mark.skipif(
    os.environ.get("ACHPRAK_TS_TESTS") != "1"
    and os.environ.get("ACHPRAK_CHEMISTRY_TESTS") != "1",
    reason="Opt-in exhaustive-screen regressions",
)
@pytest.mark.parametrize(
    "fixture",
    FAILURES,
    ids=[path.stem for path in FAILURES],
)
def test_screen_failure(fixture, tmp_path):
    case = json.loads(fixture.read_text())
    # Freeze the originally failing minimum rather than allowing a later
    # embedding/library change to silently choose a different conformer.
    if "minimum_xyz" in case:
        atoms = common.xyz_to_atoms(case["minimum_xyz"])
    else:
        if "initial_xyz" in case:
            atoms = common.xyz_to_atoms(case["initial_xyz"])
        else:
            atoms = azobenzene.Template(
                configuration=case["configuration"],
                **{
                    f"r{i // 5 + 1}c{i % 5 + 1}": s
                    for i, s in enumerate(case["substituents"])
                },
            ).atoms
        minimum = optimization.OptMin(atoms)
        assert minimum.run(steps=500), "Source minimum did not converge"
        atoms = common.xyz_to_atoms(common.atoms_to_xyz(minimum.atoms))
    search = OptTS(atoms)
    assert ts_restriction({"substituents": case["substituents"]}) is None
    max_attempts = MAX_TS_ATTEMPTS
    ok = search.run(steps=1500, max_attempts=max_attempts)
    diagnostics = tmp_path / "ts-result.json"
    diagnostics.write_text(
        json.dumps(
            {
                "id": case["id"],
                "converged": bool(ok),
                "final_xyz": common.atoms_to_xyz(search.atoms),
                "attempts": search.attempts,
                "max_attempts": max_attempts,
                "student_eligible": True,
                **{
                    key: getattr(search, key)
                    for key in (
                        "failure_reason",
                        "validation",
                        "connectivity",
                        "iterations_used",
                        "barrier_ev",
                    )
                },
            },
            indent=2,
        )
    )
    assert ok, f"{search.failure_reason}; diagnostics: {diagnostics}"
    assert search.band_converged
    assert 1 <= len(search.attempts) <= max_attempts
    assert all(a["iterations"] <= 1500 for a in search.attempts)
    assert search.iterations_used == sum(a["iterations"] for a in search.attempts)
    assert search.validation["verified"]
    frequencies = np.asarray(search.validation["frequencies_cm1"])
    assert len(frequencies) == 3 * len(atoms) - 6
    assert np.isfinite(frequencies).all()
    assert np.count_nonzero(frequencies < -20) == 1
    assert search.barrier_ev > 0
    assert search.connectivity["verified"]
    assert {b["isomer"] for b in search.connectivity["branches"]} == {"cis", "trans"}
    assert all(
        b["converged"] and b["bonds_preserved"] for b in search.connectivity["branches"]
    )
