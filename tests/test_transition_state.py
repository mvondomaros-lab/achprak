"""Physical mode classification and minimum-to-saddle workflow regressions."""

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
