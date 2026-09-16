"""Paired, opt-in comparison of TS strategies on identical saved minima.

Uses all baseline failures plus a deterministic sample of successful cases.
No production search settings or acceptance thresholds are changed.
"""

import argparse
import concurrent.futures
import contextlib
from functools import partial
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import multiprocessing
import os
from pathlib import Path
import time
import traceback

for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[variable] = "1"

from ase.mep import DyNEB
from ase.optimize import LBFGS
from achprak import common


def run(record, strategy, source):
    counts = {"calculator_calls": 0, "calculator_seconds": 0.0, "by_phase": {}}
    phase = "setup"

    class CountingCalculator(common.DefaultASECalculator):
        def calculate(self, *args, **kwargs):
            started = time.perf_counter()
            counts["calculator_calls"] += 1
            counts["by_phase"][phase] = counts["by_phase"].get(phase, 0) + 1
            try:
                return super().calculate(*args, **kwargs)
            finally:
                counts["calculator_seconds"] += time.perf_counter() - started

    def observe(atoms, step, name):
        nonlocal phase
        phase = name

    spec = importlib.util.spec_from_file_location("achprak._strategy_benchmark", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if strategy == "dynamic_neb":
        # Same 0.05 eV/A threshold on EVERY image; no distance-based loosening.
        module.NEB = partial(DyNEB, fmax=0.05, scale_fmax=0.0)
    if strategy == "lbfgs_neb":
        # Replace only band relaxation; retain seeds and all tolerances.
        def band_optimizer(atoms, *, logfile, dt, maxstep):
            return LBFGS(atoms, logfile=logfile, maxstep=maxstep, use_line_search=False)

        module.FIRE = band_optimizer
    search = module.OptTS(
        common.xyz_to_atoms(record["minimum_xyz"]), calc=CountingCalculator()
    )
    started = time.perf_counter()
    cpu_started = time.process_time()
    result = {"id": record["id"], "strategy": strategy, "converged": False}
    try:
        if strategy == "open150_lbfgs":
            # Exactly the production final fallback, attempted directly once.
            # All path, saddle, frequency and connectivity stages still run.
            ok = search._run_path(
                1500,
                observe,
                reverse=False,
                seed_angle=150.0,
                downhill_steps=50,
                use_lbfgs=True,
            )
            search.attempts = [
                {
                    "reverse_rotation": False,
                    "seed_angle_deg": 150.0,
                    "band_optimizer": "LBFGS",
                    "iterations": search.iterations_used,
                    "converged": bool(ok),
                    "failure_reason": search.failure_reason,
                }
            ]
        else:
            ok = search.run(steps=1500, observer=observe)
        result["converged"] = bool(ok)
        if result["converged"]:
            frequencies = search.validation["frequencies_cm1"]
            assert len(frequencies) == 3 * len(search.atoms) - 6
            assert all(math.isfinite(f) for f in frequencies)
            assert sum(f < -20 for f in frequencies) == 1
            assert search.validation["verified"] and search.barrier_ev > 0
            assert search.connectivity["verified"]
            branches = search.connectivity["branches"]
            assert {b["isomer"] for b in branches} == {"cis", "trans"}
            assert all(b["converged"] and b["bonds_preserved"] for b in branches)
            assert search.band_converged and len(search.path) == 13
        for name in (
            "attempts",
            "failure_reason",
            "iterations_used",
            "barrier_ev",
            "validation",
            "connectivity",
            "band_converged",
        ):
            result[name] = getattr(search, name)
        result["final_xyz"] = common.atoms_to_xyz(search.atoms)
    except Exception:
        result["converged"] = False
        result["error"] = traceback.format_exc()
    result.update(
        counts,
        seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu_started,
    )
    return result


def select_controls(records, count):
    """Balance cis/trans and mono/same-ring/cross-ring substitution patterns."""
    buckets = {}
    for record in records:
        values = record["substituents"]
        pattern = (
            "mono"
            if values.count("H") == 9
            else "cross_ring"
            if any(v != "H" for v in values[:5]) and any(v != "H" for v in values[5:])
            else "same_ring"
        )
        buckets.setdefault((record["configuration"], pattern), []).append(record)
    for bucket in buckets.values():
        bucket.sort(key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    selected = []
    while len(selected) < count:
        added = False
        for key in sorted(buckets):
            if buckets[key] and len(selected) < count:
                selected.append(buckets[key].pop(0))
                added = True
        if not added:
            break
    return selected


def run_pair(record, strategies, output, source, hashes):
    """Run both methods consecutively in one single-threaded process."""
    for name, digest in hashes.items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Benchmark source changed: {name}")
    root = Path(output)
    results = []
    for strategy in strategies:
        path = root / (record["id"] + "-" + strategy + ".json")
        if path.exists():
            results.append(json.loads(path.read_text()))
            continue
        with (
            path.with_suffix(".log").open("w") as log,
            contextlib.redirect_stdout(log),
            contextlib.redirect_stderr(log),
        ):
            result = run(record, strategy, Path(source))
        result["cohort"] = record["cohort"]
        result["strategy_order"] = strategies
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(result, indent=2, allow_nan=False))
        temporary.replace(path)
        results.append(result)
        print(
            json.dumps(
                {
                    key: result[key]
                    for key in (
                        "id",
                        "strategy",
                        "cohort",
                        "converged",
                        "seconds",
                        "calculator_calls",
                    )
                }
            ),
            flush=True,
        )
    return [r["id"] for r in results]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen", type=Path, default=Path("results/ts-screen"))
    parser.add_argument("--output", type=Path, default=Path("results/ts-strategy"))
    parser.add_argument("--controls", type=int, default=12)
    parser.add_argument("--workers", type=int, choices=range(1, 5), default=1)
    parser.add_argument(
        "--failures",
        type=Path,
        default=Path("tests/data/ts_failures"),
        help="Also retain failures from previously screened equivalent conformers",
    )
    parser.add_argument("--case", action="append", help="Restrict to explicit case IDs")
    parser.add_argument(
        "--strategy",
        choices=("current", "dynamic_neb", "lbfgs_neb", "open150_lbfgs"),
        action="append",
    )
    args = parser.parse_args()
    records = [
        json.loads(p.read_text())
        for p in args.screen.glob("*.json")
        if p.name.startswith(("cis-", "trans-"))
    ]
    records = [r for r in records if "minimum_xyz" in r]
    by_id = {r["id"]: r for r in records}
    failure_ids = set()
    for path in args.failures.glob("*.json"):
        record = json.loads(path.read_text())
        if "minimum_xyz" in record:
            # The saved failing conformer takes precedence over later results.
            by_id[record["id"]] = dict(record, converged=False)
            failure_ids.add(record["id"])
    records = list(by_id.values())
    if args.case:
        records = [r for r in records if r["id"] in args.case]
        if {r["id"] for r in records} != set(args.case):
            parser.error("Some requested cases have no saved minimum")
    else:
        controls = select_controls(
            [r for r in records if r["converged"]], args.controls
        )
        records = [r for r in records if not r["converged"]] + controls
    records.sort(key=lambda r: r["id"])
    for record in records:
        record["cohort"] = "saved_failure" if record["id"] in failure_ids else "control"
    source = Path("src/achprak/transition_state.py")
    strategies = args.strategy or ["current", "open150_lbfgs"]
    manifest = {
        "source_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (
                source,
                Path("src/achprak/common.py"),
                Path("src/achprak/azobenzene.py"),
                Path(__file__),
            )
        },
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("ase", "sella", "tblite", "numpy", "rdkit")
        },
        "minimum_sha256": {
            r["id"]: hashlib.sha256(r["minimum_xyz"].encode()).hexdigest()
            for r in records
        },
        "strategies": strategies,
        "workers": args.workers,
        "cohorts": {r["id"]: r["cohort"] for r in records},
        "order": {
            r["id"]: strategies[:: (-1 if i % 2 else 1)] for i, r in enumerate(records)
        },
        "control_selection": "stable hash within six configuration/substitution strata",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        parser.error("Benchmark inputs changed; use a new output directory")
    manifest_path.write_text(json.dumps(manifest, indent=2))
    archived = args.output / "transition_state.py"
    archived.write_bytes(source.read_bytes())
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=args.workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as pool:
        pending = [
            pool.submit(
                run_pair,
                r,
                manifest["order"][r["id"]],
                args.output,
                archived,
                manifest["source_sha256"],
            )
            for r in records
        ]
        for future in concurrent.futures.as_completed(pending):
            future.result()


if __name__ == "__main__":
    main()
