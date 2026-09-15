"""One calculation per process: no shared calculator or working directory."""

import io
import json
import os
import sys
import traceback
import uuid
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdDepictor, rdMolDescriptors
from rdkit.Chem.Draw import rdMolDraw2D

from achprak import azobenzene, common, optimization, uvvis
from achprak.transition_state import OptTS

PROGRESS_PREFIX = "ACHPRAK_PROGRESS "


def progress_observer(source_id, history):
    def publish(atoms, step, phase):
        # ASE calls observers after accepted steps. Calculator results are cached;
        # these reads do not launch extra single-point calculations.
        progress = {
            "source_id": source_id,
            "step": step,
            "phase": phase,
            "positions": atoms.positions.round(6).reshape(-1).tolist(),
            "energy_ev": float(atoms.get_potential_energy()),
            "fmax_ev_angstrom": float(
                np.linalg.norm(atoms.get_forces(apply_constraint=False), axis=1).max()
            ),
        }
        if "neb_path" in atoms.info:
            progress["neb_path"] = atoms.info["neb_path"]
            progress["neb_image"] = atoms.info["neb_image"]
        history.append(progress)
        # The frontend separates progress records from ordinary job output.
        print(PROGRESS_PREFIX + json.dumps(progress, allow_nan=False), flush=True)

    return publish


def read_atoms(xyz):
    lines = xyz.strip().splitlines()
    if not lines or not lines[0].strip().isdigit():
        raise ValueError("XYZ muss mit der Atomanzahl beginnen.")
    count = int(lines[0])
    if not 1 <= count <= 200 or len(lines) != count + 2:
        raise ValueError(
            "Erwartet wird genau eine XYZ-Struktur mit höchstens 200 Atomen."
        )
    atoms = common.xyz_to_atoms(xyz)
    if not np.isfinite(atoms.positions).all() or np.abs(atoms.positions).max() > 10000:
        raise ValueError("Ungültige Atomkoordinaten.")
    if set(atoms.get_chemical_symbols()) - {"H", "C", "N", "O", "F", "S"}:
        raise ValueError("Unterstützte Elemente: H, C, N, O, F und S.")
    return atoms


def molecule(atoms, name, kind="initial", mol=None, parent_id=None):
    mol = mol if mol is not None else common.atoms_to_mol(atoms)
    flat = Chem.RemoveHs(Chem.Mol(mol))
    rdDepictor.Compute2DCoords(flat)
    drawer = rdMolDraw2D.MolDraw2DSVG(700, 340)
    drawer.drawOptions().clearBackground = False
    drawer.DrawMolecule(flat)
    drawer.FinishDrawing()
    geometry = azobenzene.Properties(atoms.copy())
    return {
        "geometry_definition": {
            "dihedral_indices": geometry.cnnc_dihedral_indices(),
            "rings": [
                list(ring) for ring in geometry.mol.GetRingInfo().AtomRings()[:2]
            ],
            "masses": atoms.get_masses().tolist(),
        },
        "id": uuid.uuid4().hex,
        "name": name,
        "base_name": name,
        "kind": kind,
        "parent_id": parent_id,
        "xyz": common.atoms_to_xyz(atoms),
        "sdf": Chem.MolToMolBlock(mol),
        "svg": drawer.GetDrawingText(),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
        "atom_count": len(atoms),
    }


def properties(atoms):
    p = azobenzene.Properties(atoms)
    # Use the same single-point method for all structures.
    return {
        "energy_ev": float(p.energy()),
        "dihedral_deg": float(p.cnnc_dihedral()),
        "ring_distance_pm": float(p.ring_distance()),
    }


def calculate(data):
    kind = data["kind"]
    if kind not in {"template", "minimum", "ts", "uvvis"}:
        raise ValueError("Nur vordefinierte Azobenzolstrukturen werden unterstützt.")
    if kind == "template":
        settings = data["settings"]
        kwargs = {
            f"r{r + 1}c{c + 1}": settings["substituents"][r * 5 + c]
            for r in range(2)
            for c in range(5)
        }
        t = azobenzene.Template(configuration=settings["configuration"], **kwargs)
        labels = [
            f"{i % 5 + 2}{'′' if i >= 5 else ''}-{sub}"
            for i, sub in enumerate(settings["substituents"])
            if sub != "H"
        ]
        substitutions = ", ".join(labels)
        name = f"{settings['configuration']}-{substitutions + '-' if labels else ''}Azobenzol"
        m = molecule(t.atoms, name, mol=t.molh)
        m["settings"] = settings
        m["properties"] = properties(t.atoms)
        return {"molecule": m}
    source = data["molecule"]
    if kind == "minimum" and source["kind"] == "minimum":
        raise ValueError(
            "Diese Struktur ist bereits ein Minimum. Der vorhandene Verlauf bleibt erhalten."
        )
    if kind == "ts" and (source["kind"] != "minimum" or not source.get("converged")):
        raise ValueError(
            "Die Übergangszustandssuche startet von einem Minimum. Suchen Sie zuerst ein Minimum."
        )
    atoms = read_atoms(source["xyz"])
    if kind in ("minimum", "ts"):
        opt = optimization.OptMin(atoms) if kind == "minimum" else OptTS(atoms)
        history = []
        converged = bool(
            opt.run(
                steps=500 if kind == "minimum" else 1500,
                observer=progress_observer(source["id"], history),
            )
        )
        suffix = "Minimum" if kind == "minimum" else "Übergangszustand"
        if not converged:
            suffix = (
                "Minimumsuche nicht abgeschlossen"
                if kind == "minimum"
                else "Übergangszustandssuche nicht abgeschlossen"
            )
        m = molecule(
            opt.atoms,
            f"{source['base_name']} · {suffix}",
            kind if converged else "unconverged",
            parent_id=source["id"],
        )
        m["base_name"] = source["base_name"]
        m["converged"] = converged
        # Preserve every accepted step even when a short run finishes between
        # browser polls, or the bounded job log has dropped its earliest lines.
        m["optimization_history"] = history
        m["properties"] = properties(opt.atoms)
        m["frames"] = [a.positions.reshape(-1).tolist() for a in (opt.traj or [])]
        m["trajectory_kind"] = (
            "vibration" if kind == "ts" and converged else "optimization"
        )
        if kind == "ts":
            m["ts_search"] = {
                "method": "ci_neb_then_sella",
                "source_minimum_id": source["id"],
                "search_converged": opt.search_converged,
                "band_converged": opt.band_converged,
                "path": opt.path,
                "connectivity": opt.connectivity,
                "other_minimum": (
                    {
                        "xyz": common.atoms_to_xyz(opt.endpoint),
                        "energy_ev": float(opt.endpoint.get_potential_energy()),
                    }
                    if opt.endpoint is not None
                    else None
                ),
                "iterations": opt.iterations_used,
                "validation": opt.validation,
                "barrier_ev": opt.barrier_ev,
                "failure_reason": opt.failure_reason,
                "path_scope": "torsion_seeded_two_endpoint_path_not_global_barrier_search",
            }
        return {"molecule": m}
    if kind == "uvvis":
        spec = uvvis.UVVis(atoms)
        spec.calculate()
        if len(spec.excitations) == 0:
            raise RuntimeError("MOPAC hat keine elektronischen Übergänge ausgegeben.")
        energies, absorption = spec.spectrum()
        import matplotlib.pyplot as plt

        with plt.rc_context(
            {
                "font.size": 11,
                "axes.facecolor": "white",
                "figure.facecolor": "white",
                "axes.edgecolor": "#cbd7e4",
                "axes.labelcolor": "#37526e",
                "text.color": "#192d43",
                "xtick.color": "#586b80",
                "ytick.color": "#586b80",
                "grid.color": "#e7edf5",
                "svg.fonttype": "none",
            }
        ):
            fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
            ax.plot(energies, absorption, color="#165de1", linewidth=2)
            ax.fill_between(energies, absorption, color="#165de1", alpha=0.06)
            ax.vlines(
                spec.excitations,
                0,
                spec.oscillator_strengths,
                color="#d88638",
                linewidth=1.2,
                alpha=0.9,
            )
            ax.set(
                xlim=(uvvis.EMIN, uvvis.EMAX),
                ylim=(
                    0,
                    max(float(absorption.max()), float(spec.oscillator_strengths.max()))
                    * 1.15,
                ),
                xlabel="Energie / eV",
                ylabel="Absorption / a.u.",
            )
            top = ax.twiny()
            top.set_xlim(ax.get_xlim())
            wavelengths = np.array([800, 600, 500, 400, 300, 250])
            top.set_xticks(1239.8419843320026 / wavelengths, wavelengths)
            top.set_xlabel("Wellenlänge / nm")
            top.grid(False)
            image = io.StringIO()
            fig.savefig(image, format="svg")
            plt.close(fig)
        return {
            "molecule_id": source["id"],
            "spectrum": {
                "svg": image.getvalue(),
                "energy_ev": energies.tolist(),
                "absorption": absorption.tolist(),
                "excitations_ev": spec.excitations.tolist(),
                "oscillator_strengths": spec.oscillator_strengths.tolist(),
                "sigma_ev": uvvis.SIGMA,
            },
        }
    raise ValueError("Unbekannte Berechnung.")


def main():
    folder = Path(sys.argv[1]).resolve()
    os.chdir(folder)
    try:
        result = {
            "ok": True,
            "result": calculate(json.loads((folder / "input.json").read_text())),
        }
    except Exception as exc:
        traceback.print_exc()
        result = {"ok": False, "error": str(exc) or type(exc).__name__}
    temp = folder / "result.tmp"
    temp.write_text(json.dumps(result, allow_nan=False))
    temp.replace(folder / "result.json")


if __name__ == "__main__":
    main()
