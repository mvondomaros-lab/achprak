"""Resumable exhaustive template screen (opt-in, real chemistry).

Example: pixi run -e dev python scripts/screen_ts.py --scope first-ring --workers 4
Each labeled template is tested: symmetry-related labels can embed differently.
"""

import argparse
import concurrent.futures
import contextlib
import hashlib
import itertools
import json
import os
from pathlib import Path
import time
import traceback

# Set before importing numerical libraries, including in spawned workers.
for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[variable] = "1"

from achprak import azobenzene, common, optimization
from achprak.transition_state import OptTS


def cases(scope):
    groups = [s for s in azobenzene.Template.substituent_smiles if s != "H"]
    for count in (1, 2):
        positions = range(5 if count == 1 or scope == "first-ring" else 10)
        for sites in itertools.combinations(positions, count):
            for substituents in itertools.product(groups, repeat=count):
                for configuration in ("trans", "cis"):
                    values = ["H"] * 10
                    for site, group in zip(sites, substituents):
                        values[site] = group
                    labels = [f"r{i // 5 + 1}-{i % 5 + 2}-{values[i]}" for i in sites]
                    yield {"id": configuration + "-" + "_".join(labels),
                           "configuration": configuration, "substituents": values}


def run_case(case, output):
    root = Path(output)
    started = time.perf_counter()
    record = dict(case, converged=False, stage="template")
    with (root / (case["id"] + ".log")).open("w") as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            try:
                template = azobenzene.Template(
                    configuration=case["configuration"],
                    **{f"r{i // 5 + 1}c{i % 5 + 1}": s
                       for i, s in enumerate(case["substituents"])})
                # Match the web workflow's XYZ serialization between jobs.
                record["initial_xyz"] = common.atoms_to_xyz(template.atoms)
                record["stage"] = "minimum"
                minimum = optimization.OptMin(common.xyz_to_atoms(record["initial_xyz"]))
                if not minimum.run(steps=500):
                    record["failure_reason"] = "Source minimum did not converge"
                else:
                    record["minimum_xyz"] = common.atoms_to_xyz(minimum.atoms)
                    record["stage"] = "ts"
                    search = OptTS(common.xyz_to_atoms(record["minimum_xyz"]))
                    record["converged"] = bool(search.run(steps=1500))
                    for key in ("failure_reason", "iterations_used", "barrier_ev",
                                "validation", "connectivity", "band_converged"):
                        record[key] = getattr(search, key)
                    record["final_xyz"] = common.atoms_to_xyz(search.atoms)
            except Exception:
                record["error"] = traceback.format_exc()
    record["seconds"] = time.perf_counter() - started
    temporary = root / (case["id"] + ".json.tmp")
    temporary.write_text(json.dumps(record, indent=2, allow_nan=False))
    temporary.replace(root / (case["id"] + ".json"))
    return {key: record.get(key) for key in ("id", "converged", "stage", "seconds", "failure_reason", "error")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("mono", "first-ring", "both-rings"), default="both-rings")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", default="results/ts-screen")
    parser.add_argument("--case", help="Run one case by its exact ID")
    parser.add_argument("--only-disubstituted", action="store_true")
    parser.add_argument("--collect-failures", action="store_true",
                        help="Save completed failures as deterministic opt-in test fixtures, then exit")
    args = parser.parse_args()
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.collect_failures:
        fixtures = Path(__file__).resolve().parents[1] / "tests/data/ts_failures"
        fixtures.mkdir(parents=True, exist_ok=True)
        for path in sorted(root.glob("*.json")):
            record = json.loads(path.read_text())
            if record.get("converged") is not False:
                continue
            fixture = fixtures / path.name
            if not fixture.exists():
                fixture.write_text(json.dumps({key: record[key] for key in (
                    "id", "configuration", "substituents", "initial_xyz", "minimum_xyz",
                    "stage", "failure_reason", "error") if key in record}, indent=2))
                print(f"Added {fixture.name}")
        return
    selected = [c for c in cases(args.scope)
                if (args.scope != "mono" or c["substituents"].count("H") == 9)
                and (not args.only_disubstituted or c["substituents"].count("H") == 8)
                and (not args.case or c["id"] == args.case)]
    if not selected:
        parser.error("No matching cases")
    manifest = {"scope": args.scope, "count": len(selected), "seed": 42,
                "method": "GFN1-xTB", "solvent": "ALPB ethanol",
                "source_sha256": {name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
                    for name in ("src/achprak/transition_state.py", "src/achprak/optimization.py", "src/achprak/azobenzene.py")},
                "cases": selected}
    (root / f"manifest-{args.scope}.json").write_text(json.dumps(manifest, indent=2))
    pending = [c for c in selected if not (root / (c["id"] + ".json")).exists()]
    print(f"{len(selected)} cases; {len(pending)} pending", flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_case, case, str(root)) for case in pending]
        for future in concurrent.futures.as_completed(futures):
            print(json.dumps(future.result()), flush=True)


if __name__ == "__main__":
    main()
