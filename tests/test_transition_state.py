"""Physical mode classification and minimum-to-saddle workflow regressions."""

import json
from pathlib import Path

import numpy as np
import pytest
from ase import Atoms

from achprak.transition_state import internal_modes


def test_rigid_motion_projection_and_coordinate_invariance():
    atoms = Atoms("CHHH", positions=[[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]])
    # A negative curvature along a bond stretch; all other directions stable.
    stretch = np.zeros((4, 3))
    stretch[0, 0], stretch[1, 0] = -1, 1
    v = stretch.ravel() / np.linalg.norm(stretch)
    hessian = np.eye(12) - 10 * np.outer(v, v)
    frequencies, modes = internal_modes(atoms, hessian)
    assert len(frequencies) == 6  # 3N - 6, no translations or rotations.
    assert np.count_nonzero(frequencies < 0) == 1
    assert modes.shape == (6, 4, 3)
    angle = 0.63
    rotation = np.array(
        [
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1],
        ]
    )
    moved = atoms.copy()
    moved.positions = atoms.positions @ rotation.T + [7, -4, 3]
    transform = np.kron(np.eye(4), rotation)
    rotated, _ = internal_modes(moved, transform @ hessian @ transform.T)
    np.testing.assert_allclose(frequencies, rotated, atol=1e-8)
    positive, _ = internal_modes(atoms, np.eye(12))
    assert np.all(positive > 0)


def test_ts_worker_rejects_start_structures_before_search():
    from achprak.web.worker import calculate

    with pytest.raises(ValueError, match="Minimum"):
        calculate({"kind": "ts", "molecule": {"kind": "initial", "converged": False}})


def test_path_records_use_cumulative_distance_and_preserve_atom_order():
    from ase.calculators.singlepoint import SinglePointCalculator
    from achprak.transition_state import OptTS

    images = []
    for x, energy in [(0, -2), (1, -1), (3, -1.5)]:
        atoms = Atoms("CH", positions=[[x, 0, 0], [x, 1, 0]])
        atoms.calc = SinglePointCalculator(atoms, energy=energy)
        images.append(atoms)
    path = OptTS.path_records(images)
    np.testing.assert_allclose([p["coordinate"] for p in path], [0, 1 / 3, 1])
    assert [p["energy_ev"] for p in path] == [-2, -1, -1.5]
    assert path[-1]["positions"] == [3, 0, 0, 3, 1, 0]


def test_bond_graph_does_not_replace_the_energy_calculator():
    from ase.calculators.singlepoint import SinglePointCalculator
    from achprak.transition_state import OptTS

    atoms = Atoms("HH", positions=[[0, 0, 0], [0, 0, 0.74]])
    calculator = SinglePointCalculator(atoms, energy=-1.0)
    atoms.calc = calculator
    assert OptTS.bond_graph(atoms) == {(0, 1, 1.0)}
    assert atoms.calc is calculator
    assert atoms.get_potential_energy() == -1.0


def test_close_sulfur_nitrogen_contact_preserves_template_connectivity():
    from achprak import common
    from achprak.transition_state import OptTS

    case = json.loads(
        (
            Path(__file__).parent / "data/ts_failures/trans-r1-2-SO2CF3_r1-6-NMe2.json"
        ).read_text()
    )
    initial = common.xyz_to_atoms(case["initial_xyz"])
    minimum = common.xyz_to_atoms(case["minimum_xyz"])
    assert minimum.get_distance(1, 17) < 2.14
    assert OptTS.bond_graph(minimum) == OptTS.bond_graph(initial)
    # Fragment rotation must not cross the nonbonded S...N contact and pick
    # up atoms from the substituted ring on the other side of N=N.
    search = OptTS(minimum)
    assert search.indices[0] not in search.rotating_indices
    assert search.indices[3] in search.rotating_indices


@pytest.mark.parametrize("failure_kind", ["endpoint", "path", "connectivity"])
@pytest.mark.parametrize("succeed_on", [1, 2, 4, None])
@pytest.mark.parametrize("max_attempts", [1, 2, 4])
def test_seed_retries_restore_source_and_account_for_all_work(
    monkeypatch, failure_kind, succeed_on, max_attempts
):
    from achprak.transition_state import OptTS

    search = object.__new__(OptTS)
    search.atoms = Atoms("HH", positions=[[0, 0, 0], [0, 0, 0.74]])
    source = search.atoms.positions.copy()
    seeds, observed = [], []

    def attempt(self, steps, observer, **seed):
        np.testing.assert_array_equal(self.atoms.positions, source)
        assert steps == 7
        seeds.append(seed)
        self.atoms.positions += len(seeds)
        self.search_traj = [self.atoms.copy()]
        self.traj = [self.atoms.copy()]
        self.iterations_used = len(seeds)
        self.endpoint = self.atoms.copy() if failure_kind != "endpoint" else None
        self.connectivity = (
            {"branches": [{"bonds_preserved": False}]}
            if failure_kind == "connectivity"
            else None
        )
        ok = len(seeds) == succeed_on
        self.failure_reason = None if ok else "Test failure"
        observer(self.atoms, 0, "endpoint")
        return ok

    monkeypatch.setattr(OptTS, "_run_path", attempt)
    assert search.run(
        steps=7,
        observer=lambda a, i, p: observed.append((i, a.info["ts_attempt"])),
        max_attempts=max_attempts,
    ) == (succeed_on is not None and succeed_on <= max_attempts)
    count = min(succeed_on or 4, max_attempts)
    assert search.max_attempts == max_attempts
    assert len(search.attempts) == count
    assert search.iterations_used == sum(range(1, count + 1))
    assert observed == list(enumerate(range(1, count + 1)))
    assert len(search.search_traj) == count
    assert seeds[0]["use_lbfgs"] is False
    assert all(seed["use_lbfgs"] for seed in seeds[1:])
    assert [a["band_optimizer"] for a in search.attempts] == ["FIRE"] + ["LBFGS"] * (
        count - 1
    )
    if count > 1:
        assert seeds[1]["reverse"] == (failure_kind == "path")
        assert seeds[1]["seed_angle"] == (120 if failure_kind == "path" else 135)
    if count == 4:
        assert seeds[-1]["seed_angle"] == 150
        assert seeds[-1]["reverse"] is False
    if succeed_on is None or succeed_on > max_attempts:
        assert len(search.traj) == count
