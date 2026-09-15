"""Check trans-azobenzene ring twists and curvature at tight xTB geometries."""

import contextlib
import json
from pathlib import Path

import numpy as np
from ase.optimize import BFGS
from ase.vibrations import Vibrations

from achprak import azobenzene, common
from achprak.transition_state import internal_modes


def geometry_metrics(atoms):
    properties = azobenzene.Properties(atoms.copy())
    c1, n1, n2, c2 = properties.cnnc_dihedral_indices()
    heavy = atoms.positions[atoms.numbers != 1]
    relative = heavy - heavy.mean(axis=0)
    _, _, axes = np.linalg.svd(relative)
    distances = relative @ axes[-1]
    twists = []
    rings = properties.mol.GetRingInfo().AtomRings()
    for carbon, nitrogen, other in ((c1, n1, n2), (c2, n2, n1)):
        ring = next(r for r in rings if carbon in r)
        neighbor = next(
            a.GetIdx()
            for a in properties.mol.GetAtomWithIdx(carbon).GetNeighbors()
            if a.GetIdx() in ring
        )
        angle = float(atoms.get_dihedral(neighbor, carbon, nitrogen, other))
        twists.append(min(angle, abs(angle - 180), 360 - angle))
    return {
        "cnnc_deg": float(atoms.get_dihedral(c1, n1, n2, c2)),
        "ring_twists_deg": twists,
        "heavy_plane_rms_angstrom": float(np.sqrt(np.mean(distances**2))),
        "heavy_plane_max_angstrom": float(abs(distances).max()),
    }


def main():
    root = Path("results/science-benchmark").resolve()
    records = json.loads((root / "report.json").read_text())
    result = []
    for record in records:
        if record["case"] != "trans-H":
            continue
        for planar in (False, True):
            atoms = common.xyz_to_atoms(record["tight_xyz"])
            if planar:
                center = atoms.positions.mean(axis=0)
                relative = atoms.positions - center
                _, _, axes = np.linalg.svd(relative)
                atoms.positions -= (relative @ axes[-1])[:, None] * axes[-1]
            atoms.calc = common.DefaultASECalculator(
                method=record["method"], accuracy=0.1
            )
            with (
                (root / f"planarity-{record['method']}-{planar}.log").open("w") as log,
                contextlib.redirect_stdout(log),
            ):
                with BFGS(atoms, maxstep=0.05, logfile=log) as opt:
                    converged = bool(opt.run(fmax=0.0001, steps=500))
                with common.tempdir():
                    vibrations = Vibrations(atoms, delta=0.01)
                    vibrations.run()
                    frequencies, _ = internal_modes(
                        atoms, vibrations.get_vibrations().get_hessian_2d()
                    )
            result.append(
                {
                    "method": record["method"],
                    "planar_seed": planar,
                    "converged": converged,
                    "fmax": 0.0001,
                    "actual_fmax": float(
                        np.linalg.norm(atoms.get_forces(), axis=1).max()
                    ),
                    "energy_ev": float(atoms.get_potential_energy()),
                    "frequencies_cm1": frequencies.tolist(),
                    "xyz": common.atoms_to_xyz(atoms),
                    **geometry_metrics(atoms),
                }
            )
            (root / "planarity.json").write_text(json.dumps(result, indent=2))
            print(
                {
                    k: v
                    for k, v in result[-1].items()
                    if k not in {"xyz", "frequencies_cm1"}
                },
                flush=True,
            )


if __name__ == "__main__":
    main()
