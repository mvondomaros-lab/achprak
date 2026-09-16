"""Resumable exhaustive template screen (opt-in, real chemistry).

Example: pixi run -e dev python scripts/screen_ts.py --scope first-ring --workers 4
Each labeled template is tested: symmetry-related labels can embed differently.
"""

import argparse
import concurrent.futures
import contextlib
import csv
import hashlib
import importlib.metadata
import importlib.util
import itertools
import json
import os
import platform
from pathlib import Path
import time
import traceback

# Set before importing numerical libraries, including in spawned workers.
for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[variable] = "1"

from achprak import azobenzene, common, optimization
from achprak.transition_state import OptTS


def cases(scope):
    # Historical screen: preserve its case IDs and cached-result provenance.
    # CN/NO2 in the revised course menu have not undergone this exhaustive screen.
    groups = ["Me", "NMe2", "CF3", "OMe", "F", "SO2CF3"]
    for count in (1, 2):
        positions = range(5 if count == 1 or scope == "first-ring" else 10)
        for sites in itertools.combinations(positions, count):
            for substituents in itertools.product(groups, repeat=count):
                for configuration in ("trans", "cis"):
                    values = ["H"] * 10
                    for site, group in zip(sites, substituents):
                        values[site] = group
                    labels = [f"r{i // 5 + 1}-{i % 5 + 2}-{values[i]}" for i in sites]
                    yield {
                        "id": configuration + "-" + "_".join(labels),
                        "configuration": configuration,
                        "substituents": values,
                    }


def symmetry_key(case):
    """Constitutional identity under ring reflections and ring exchange.

    Keep cis/trans distinct. This identifies substitution patterns, not local
    conformers, and does not claim equivalent embeddings share a TS outcome.
    """
    first, second = tuple(case["substituents"][:5]), tuple(case["substituents"][5:])
    variants = []
    for a in (first, first[::-1]):
        for b in (second, second[::-1]):
            variants.extend((a + b, b + a))
    return case["configuration"], min(variants)


def unique_cases(selected, root):
    groups = {}
    for case in selected:
        groups.setdefault(symmetry_key(case), []).append(case)
    representatives = []
    for equivalent in groups.values():
        # Reuse an actual completed calculation without relabeling its atoms.
        representative = next(
            (c for c in equivalent if (root / (c["id"] + ".json")).exists()),
            equivalent[0],
        )
        representatives.append(
            dict(representative, equivalent_ids=[c["id"] for c in equivalent])
        )
    return representatives


def run_case(case, output, implementation=None):
    root = Path(output)
    started = time.perf_counter()
    record = dict(case, converged=False, stage="template")
    search_class = OptTS
    if implementation:
        spec = importlib.util.spec_from_file_location(
            "achprak._screen_ts", implementation
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        search_class = module.OptTS
    with (root / (case["id"] + ".log")).open("w") as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            try:
                template = azobenzene.Template(
                    configuration=case["configuration"],
                    **{
                        f"r{i // 5 + 1}c{i % 5 + 1}": s
                        for i, s in enumerate(case["substituents"])
                    },
                )
                # Match the web workflow's XYZ serialization between jobs.
                record["initial_xyz"] = common.atoms_to_xyz(template.atoms)
                record["stage"] = "minimum"
                minimum = optimization.OptMin(
                    common.xyz_to_atoms(record["initial_xyz"])
                )
                if not minimum.run(steps=500):
                    record["failure_reason"] = "Source minimum did not converge"
                else:
                    record["minimum_xyz"] = common.atoms_to_xyz(minimum.atoms)
                    angle = azobenzene.Properties(minimum.atoms.copy()).cnnc_dihedral()
                    record["minimum_dihedral_deg"] = float(angle)
                    record["minimum_configuration"] = (
                        "cis" if angle < 90 or angle > 270 else "trans"
                    )
                    record["stage"] = "ts"
                    search = search_class(common.xyz_to_atoms(record["minimum_xyz"]))
                    record["converged"] = bool(search.run(steps=1500))
                    for key in (
                        "failure_reason",
                        "iterations_used",
                        "barrier_ev",
                        "validation",
                        "connectivity",
                        "band_converged",
                    ):
                        record[key] = getattr(search, key)
                    record["final_xyz"] = common.atoms_to_xyz(search.atoms)
                    if hasattr(search, "attempts"):
                        record["attempts"] = search.attempts
            except Exception:
                record["error"] = traceback.format_exc()
    record["seconds"] = time.perf_counter() - started
    temporary = root / (case["id"] + ".json.tmp")
    temporary.write_text(json.dumps(record, indent=2, allow_nan=False))
    temporary.replace(root / (case["id"] + ".json"))
    return {
        key: record.get(key)
        for key in ("id", "converged", "stage", "seconds", "failure_reason", "error")
    }


def summarize(root, selected):
    records = []
    for case in selected:
        path = root / (case["id"] + ".json")
        if path.exists():
            records.append(json.loads(path.read_text()))
    failures = [
        {key: r.get(key) for key in ("id", "stage", "failure_reason", "error")}
        for r in records
        if not r["converged"]
    ]
    by_id = {record["id"]: record for record in records}
    with (root / "summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=(
                "id",
                "configuration",
                "status",
                "stage",
                "barrier_ev",
                "iterations_used",
                "seconds",
                "failure_reason",
                "error",
            ),
        )
        writer.writeheader()
        for case in selected:
            record = by_id.get(case["id"], {})
            row = {key: record.get(key) for key in writer.fieldnames}
            row.update(
                id=case["id"],
                configuration=case["configuration"],
                status=("passed" if record["converged"] else "failed")
                if record
                else "pending",
            )
            writer.writerow(row)
    return {
        "total": len(selected),
        "completed": len(records),
        "passed": sum(r["converged"] for r in records),
        "failed": len(failures),
        "pending": len(selected) - len(records),
        "failures": failures,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scope", choices=("mono", "first-ring", "both-rings"), default="first-ring"
    )
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--output", default="results/ts-screen")
    parser.add_argument("--case", help="Run one case by its exact ID")
    parser.add_argument("--only-disubstituted", action="store_true")
    parser.add_argument(
        "--unique",
        action="store_true",
        help="Deduplicate ring reflections and ring exchange, retaining cis/trans",
    )
    parser.add_argument(
        "--collect-failures",
        action="store_true",
        help="Save completed failures as deterministic opt-in test fixtures, then exit",
    )
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument(
        "--implementation", help="Frozen transition_state.py for baseline continuation"
    )
    args = parser.parse_args()
    root = Path(args.output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    implementation = (
        str(Path(args.implementation).resolve()) if args.implementation else None
    )
    if args.collect_failures:
        fixtures = Path(__file__).resolve().parents[1] / "tests/data/ts_failures"
        fixtures.mkdir(parents=True, exist_ok=True)
        for path in sorted(root.glob("*.json")):
            record = json.loads(path.read_text())
            if record.get("converged") is not False:
                continue
            fixture = fixtures / path.name
            if not fixture.exists():
                fixture.write_text(
                    json.dumps(
                        {
                            key: record[key]
                            for key in (
                                "id",
                                "configuration",
                                "substituents",
                                "initial_xyz",
                                "minimum_xyz",
                                "stage",
                                "failure_reason",
                                "error",
                            )
                            if key in record
                        },
                        indent=2,
                    )
                )
                print(f"Added {fixture.name}")
        return
    selected = [
        c
        for c in cases(args.scope)
        if (args.scope != "mono" or c["substituents"].count("H") == 9)
        and (not args.only_disubstituted or c["substituents"].count("H") == 8)
        and (not args.case or c["id"] == args.case)
    ]
    if not selected:
        parser.error("No matching cases")
    if args.unique:
        selected = unique_cases(selected, root)
    if args.summarize:
        summary = summarize(root, selected)
        (root / "summary.json").write_text(json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
        return
    manifest = {
        "scope": args.scope,
        "count": len(selected),
        "symmetry_unique": args.unique,
        "seed": 42,
        "method": "GFN1-xTB",
        "solvent": "ALPB ethanol",
        "platform": platform.platform(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in ("numpy", "ase", "rdkit", "tblite", "sella")
        },
        "source_sha256": {
            name: hashlib.sha256(Path(name).read_bytes()).hexdigest()
            for name in (
                implementation or "src/achprak/transition_state.py",
                "src/achprak/optimization.py",
                "src/achprak/azobenzene.py",
            )
        },
        "cases": selected,
    }
    for path in root.glob("manifest-*.json"):
        previous = json.loads(path.read_text())
        # A frozen implementation can have a different filename; compare its
        # content along with both geometry-producing modules.
        if sorted(previous["source_sha256"].values()) != sorted(
            manifest["source_sha256"].values()
        ) or (
            previous.get("packages") and previous["packages"] != manifest["packages"]
        ):
            parser.error(
                "Existing results use different code or package versions. "
                "Use a new --output directory, or the original --implementation."
            )
    selection = args.scope
    if args.unique:
        selection += "-unique"
    if args.only_disubstituted:
        selection += "-disubstituted"
    if args.case:
        selection += "-" + args.case
    (root / f"manifest-{selection}.json").write_text(json.dumps(manifest, indent=2))
    pending = [c for c in selected if not (root / (c["id"] + ".json")).exists()]
    print(f"{len(selected)} cases; {len(pending)} pending", flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(run_case, case, str(root), implementation) for case in pending
        ]
        for future in concurrent.futures.as_completed(futures):
            print(json.dumps(future.result()), flush=True)
    (root / "summary.json").write_text(json.dumps(summarize(root, selected), indent=2))


if __name__ == "__main__":
    main()
