"""Offline sensitivity benchmark; deliberately excluded from default tests.

Run with: pixi run -e dev python scripts/benchmark_science.py
Results include timings, geometries and individual transitions for independent review.
This measures numerical/method sensitivity, not accuracy against experiment.
"""

import contextlib
import json
import importlib.metadata
import os
import platform
import time
from pathlib import Path

import pymopac
import sella
from rdkit.Chem import AllChem

from achprak import azobenzene, common, uvvis


class BenchmarkTemplate(azobenzene.Template):
    """Include the sulfonyl comparison used by this offline sensitivity study."""

    substituent_smiles = {
        **azobenzene.Template.substituent_smiles,
        "SO2CF3": "(S(=O)(=O)C(F)(F)F)",
    }


CASES = [
    ("trans-H", "trans", {}, 42),
    ("cis-H", "cis", {}, 42),
    ("trans-2-Me", "trans", {"r1c1": "Me"}, 42),
    ("cis-2-Me", "cis", {"r1c1": "Me"}, 42),
    ("trans-4-NMe2", "trans", {"r1c3": "NMe2"}, 42),
    ("trans-push-pull", "trans", {"r1c3": "NMe2", "r2c3": "CF3"}, 42),
    ("trans-push-pull-seed7", "trans", {"r1c3": "NMe2", "r2c3": "CF3"}, 7),
    ("cis-2-OMe", "cis", {"r1c1": "OMe"}, 42),
    ("cis-2-OMe-seed7", "cis", {"r1c1": "OMe"}, 7),
    ("trans-sulfonyl", "trans", {"r1c3": "NMe2", "r2c3": "SO2CF3"}, 42),
]


def spectrum(atoms, maxci, folder):
    start = time.perf_counter()
    job = pymopac.MopacInput(
        common.atoms_to_xyz(atoms),
        model=f"INDO CIS MAXCI={maxci} WRTCI=200 WRTCONF=0.2 EPS=24.3",
        path=str(folder),
        addHs=False,
        preopt=False,
        aux=False,
        stream=False,
    )
    job.run()
    energies, strengths = uvvis.parse_mopac_excitations(job.outpath)
    return {
        "seconds": time.perf_counter() - start,
        "energies_ev": energies.tolist(),
        "strengths": strengths.tolist(),
    }


def main():
    root = Path("results/science-benchmark").resolve()
    root.mkdir(parents=True, exist_ok=True)
    metadata = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "ase", "rdkit", "tblite", "sella", "pymopac")
        },
        "mopac": pymopac.__mopac_version__,
        "threads": {
            name: os.environ.get(name)
            for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")
        },
    }
    (root / "environment.json").write_text(json.dumps(metadata, indent=2))
    report = []
    for name, configuration, substitutions, seed in CASES:
        template = BenchmarkTemplate(configuration=configuration, **substitutions)
        if seed != 42:
            params = AllChem.ETKDGv3()
            params.randomSeed = seed
            if AllChem.EmbedMolecule(template.molh, params) != 0:
                raise RuntimeError(f"Embedding failed: {name}")
            template.atoms = common.mol_to_atoms(template.molh)
        for method in ("GFN1-xTB", "GFN2-xTB"):
            folder = root / f"{name}-{method}"
            folder.mkdir(exist_ok=True)
            record = {"case": name, "method": method, "seed": seed}
            atoms = template.atoms.copy()
            atoms.calc = common.DefaultASECalculator(method=method, accuracy=0.1)
            start = time.perf_counter()
            with (
                (folder / "optimization.log").open("w") as log,
                contextlib.redirect_stdout(log),
            ):
                with sella.Sella(atoms, order=0, internal=True, logfile=log) as opt:
                    record["loose_converged"] = bool(opt.run(fmax=0.01, steps=500))
                    record["loose_steps"] = opt.nsteps
                    record["loose_seconds"] = time.perf_counter() - start
                    loose = atoms.copy()
                    record["loose_energy_ev"] = float(atoms.get_potential_energy())
                    record["tight_converged"] = bool(opt.run(fmax=0.002, steps=500))
                    record["tight_extra_steps"] = opt.nsteps - record["loose_steps"]
            record["total_seconds"] = time.perf_counter() - start
            record["tight_energy_ev"] = float(atoms.get_potential_energy())
            record["loose_xyz"] = common.atoms_to_xyz(loose)
            record["tight_xyz"] = common.atoms_to_xyz(atoms)
            record["dihedral_deg"] = float(
                atoms.get_dihedral(
                    *azobenzene.Properties(atoms.copy()).cnnc_dihedral_indices()
                )
            )
            comparison = atoms.copy()
            comparison.calc = common.DefaultASECalculator(method=method, accuracy=1.0)
            record["accuracy1_energy_ev"] = float(comparison.get_potential_energy())
            for label, geometry, maxci in (
                ("loose_800", loose, 800),
                ("tight_800", atoms, 800),
                ("tight_2000", atoms, 2000),
            ):
                record[label] = spectrum(geometry, maxci, folder / label)
            report.append(record)
            (root / "report.json").write_text(
                json.dumps(report, indent=2, allow_nan=False)
            )
            print(
                f"{name} {method}: {record['loose_steps']} + {record['tight_extra_steps']} steps, {record['total_seconds']:.2f} s",
                flush=True,
            )


if __name__ == "__main__":
    main()
