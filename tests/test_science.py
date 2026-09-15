"""Opt-in scientific guardrails for the teaching model."""

import os

import numpy as np
import pytest

from achprak import azobenzene, optimization


@pytest.mark.skipif(
    os.environ.get("ACHPRAK_SCIENCE_TESTS") != "1",
    reason="Opt-in real chemistry model checks",
)
def test_parent_trans_is_nearly_planar_and_lower_than_cis():
    energies = {}
    for configuration in ("trans", "cis"):
        atoms = azobenzene.Template(configuration=configuration).atoms
        opt = optimization.OptMin(atoms)
        assert opt.run()
        energies[configuration] = float(atoms.get_potential_energy())
        if configuration == "trans":
            heavy = atoms.positions[atoms.numbers != 1]
            relative = heavy - heavy.mean(axis=0)
            _, _, axes = np.linalg.svd(relative)
            rms = np.sqrt(np.mean((relative @ axes[-1]) ** 2))
            # Approximate planarity at the app's finite force threshold.
            assert rms < 0.05, f"trans heavy-atom plane RMS deviation: {rms} Å"
    assert energies["cis"] > energies["trans"]
