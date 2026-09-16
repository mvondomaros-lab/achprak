"""Summarize the reproducible local numerical sensitivity benchmark."""

import json
from pathlib import Path

import numpy as np


def peak(spec, sigma=0.15):
    energy = np.linspace(1.5, 5.5, 1000)
    transitions = np.array(spec["energies_ev"])
    strengths = np.array(spec["strengths"])
    curve = (
        np.exp(-0.5 * ((energy[:, None] - transitions) / sigma) ** 2) * strengths
    ).sum(axis=1)
    return float(energy[curve.argmax()])


def main():
    root = Path("results/science-benchmark")
    records = json.loads((root / "report.json").read_text())
    text = [
        "# Scientific settings benchmark",
        "",
        "## Scope",
        "",
        "Local sensitivity study using the locked Pixi dev environment, one BLAS/OpenMP thread, "
        "ALPB ethanol geometries, xTB accuracy 0.1, and INDO/S–CIS with COSMO EPS=24.3. "
        "The initial embedding uses ETKDGv3 with seed 42 unless stated. "
        "The same optimization continues from 0.01 to 0.002 eV/Å. "
        "This measures the incremental cost of tightening, not two independent full runs. "
        "Timings are single runs on this machine and include concurrent benchmark/test load.",
        "",
        "The push-pull case is trans-4-NMe2-4′-CF3 azobenzene; the sulfonyl case "
        "is trans-4-NMe2-4′-SO2CF3 azobenzene. Other substituent positions are "
        "given in the case names. All unspecified sites carry hydrogen.",
        "",
        "This is not validation against experiment or higher-level reference chemistry. "
        "Method differences establish sensitivity, not which method is more accurate. "
        "Spectral peaks below refer to the strongest broadened maximum in 1.5–5.5 eV, "
        "with sigma 0.15 eV; peak identity can change when bands exchange intensity.",
        "",
        "Reproduce with `pixi run -e dev python scripts/benchmark_science.py`, then "
        "`pixi run -e dev python scripts/benchmark_ts_methods.py`, and "
        "`pixi run -e dev python scripts/summarize_science_benchmark.py`. "
        "Set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` for comparable timings. "
        "Raw geometries, transition energies, oscillator strengths and logs are written "
        "under `results/science-benchmark/`. These expensive calculations are excluded from default tests.",
        "",
        "## Geometry convergence",
        "",
        "Energy change is E(loose) − E(tight). All rows retain the same molecular composition and method.",
        "",
        "| Molecule | Method | Converged loose/tight | Steps loose + extra | Extra time / s | Energy change / kJ mol⁻¹ | Spectral peak change / eV |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in records:
        text.append(
            f"| {r['case']} | {r['method']} | {r['loose_converged']}/{r['tight_converged']} | "
            f"{r['loose_steps']} + {r['tight_extra_steps']} | {r['total_seconds'] - r['loose_seconds']:.3f} | "
            f"{(r['loose_energy_ev'] - r['tight_energy_ev']) * 96.485332:.4f} | "
            f"{peak(r['loose_800']) - peak(r['tight_800']):+.4f} |"
        )
    text += [
        "",
        "## Configuration cutoff and output coverage",
        "",
        "Shifts are 800 minus 2000 configurations at the same tight geometry. "
        "Both runs request WRTCI=200 (199 transitions in this MOPAC build). "
        "WRTCI=30 output contains 29 transitions. "
        "The plotted upper limit plus four Gaussian standard deviations is 6.1 eV.",
        "",
        "| Molecule | Geometry method | First excitation shift / eV | Peak shift / eV | 800 / 2000 time / s | Last transition with WRTCI=30 / eV |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in records:
        a, b = r["tight_800"], r["tight_2000"]
        text.append(
            f"| {r['case']} | {r['method']} | {a['energies_ev'][0] - b['energies_ev'][0]:+.4f} | "
            f"{peak(a) - peak(b):+.4f} | {a['seconds']:.2f} / {b['seconds']:.2f} | {a['energies_ev'][28]:.3f} |"
        )
    text += [
        "",
        "## Method sensitivity",
        "",
        "Absolute total energies from different xTB methods must not be compared. "
        "Spectral peak changes below use the same INDO/S–CIS/800 method on the two optimized geometries.",
        "",
        "| Molecule | GFN1 geometry peak / eV | GFN2 geometry peak / eV |",
        "|---|---:|---:|",
    ]
    for a in records:
        if a["method"] != "GFN1-xTB":
            continue
        b = next(
            (
                r
                for r in records
                if r["case"] == a["case"] and r["method"] == "GFN2-xTB"
            ),
            None,
        )
        if b:
            text.append(
                f"| {a['case']} | {peak(a['tight_800']):.4f} | {peak(b['tight_800']):.4f} |"
            )
    text += [
        "",
        "The largest absolute energy change from evaluating the tight geometry with "
        f"xTB accuracy 1.0 instead of 0.1 is {max(abs(r['accuracy1_energy_ev'] - r['tight_energy_ev']) for r in records):.3g} eV. "
        "The app uses 0.1 for both geometry optimization and final energy reporting.",
    ]
    text += [
        "",
        "## Parent-isomer energy ordering",
        "",
        "Differences are E(cis) − E(trans), each calculated within one method. "
        "They include the implicit-solvent model and omit nuclear thermal corrections.",
        "",
    ]
    for method in ("GFN1-xTB", "GFN2-xTB"):
        pair = {
            r["case"]: r
            for r in records
            if r["method"] == method and r["case"] in {"cis-H", "trans-H"}
        }
        if len(pair) == 2:
            delta = (
                pair["cis-H"]["tight_energy_ev"] - pair["trans-H"]["tight_energy_ev"]
            ) * 96.485332
            text.append(f"- {method}: {delta:+.2f} kJ/mol.")
    text += [
        "",
        "## Alternative starting conformations",
        "",
        "Seed 7 minus seed 42, within the same method and composition. "
        "Two seeds sample sensitivity; they do not establish a global minimum or an ensemble spectrum.",
        "",
        "| Molecule | Method | Energy difference / kJ mol⁻¹ | Spectral peak difference / eV |",
        "|---|---|---:|---:|",
    ]
    for method in ("GFN1-xTB", "GFN2-xTB"):
        for case in ("trans-push-pull", "cis-2-OMe"):
            pair = [
                next(
                    (
                        r
                        for r in records
                        if r["case"] == case + suffix and r["method"] == method
                    ),
                    None,
                )
                for suffix in ("", "-seed7")
            ]
            if all(pair):
                a, b = pair
                text.append(
                    f"| {case} | {method} | {(b['tight_energy_ev'] - a['tight_energy_ev']) * 96.485332:+.4f} | "
                    f"{peak(b['tight_800']) - peak(a['tight_800']):+.4f} |"
                )
    if (root / "planarity.json").exists():
        text += [
            "",
            "## Parent trans planarity",
            "",
            "Unconstrained Cartesian BFGS refinement to 0.0001 eV/Å, including a second "
            "run starting from coordinates projected onto a plane. Ring twist measures "
            "the departure of an adjacent ring C–C–N–N torsion from 0° or 180°; "
            "CNNC alone does not measure phenyl-ring planarity. "
            "Full finite-difference Hessians use 0.01 Å displacement and rigid-mode projection. "
            "Reproduce with `pixi run -e dev python scripts/benchmark_planarity.py` before summarizing.",
            "",
            "| Method | Planar seed | Converged | Ring twists / ° | Heavy-atom plane RMS / Å | Lowest internal frequency / cm⁻¹ |",
            "|---|---|---|---:|---:|---:|",
        ]
        for r in json.loads((root / "planarity.json").read_text()):
            text.append(
                f"| {r['method']} | {r['planar_seed']} | {r['converged']} | "
                f"{r['ring_twists_deg'][0]:.2f}, {r['ring_twists_deg'][1]:.2f} | "
                f"{r['heavy_plane_rms_angstrom']:.4f} | {min(r['frequencies_cm1']):.2f} |"
            )
    if (root / "ts-methods.json").exists():
        text += [
            "",
            "## GFN2-xTB transition-state checks",
            "",
            "| Molecule | Confirmed TS | Time / s | Iterations | Barrier / eV | Failure |",
            "|---|---|---:|---:|---:|---|",
        ]
        for r in json.loads((root / "ts-methods.json").read_text()):
            text.append(
                f"| {r['case']} | {r['converged']} | {r['seconds']:.1f} | {r.get('iterations', '—')} | "
                f"{r.get('barrier_ev')} | {r.get('failure_reason') or r.get('error') or '—'} |"
            )
    Path("docs").mkdir(exist_ok=True)
    if (root / "environment.json").exists():
        text += [
            "",
            "## Recorded environment",
            "",
            "```json",
            (root / "environment.json").read_text(),
            "```",
        ]
    Path("docs/science-benchmark.md").write_text("\n".join(text) + "\n")


if __name__ == "__main__":
    main()
