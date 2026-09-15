"""Optional GFN2-xTB TS comparison, using geometries from benchmark_science.py.

Run after the geometry benchmark. The regular test-ts task covers GFN1-xTB.
Numerical success does not establish experimental barrier accuracy.
"""

import contextlib
import json
import time
from pathlib import Path

from achprak import common
from achprak.transition_state import OptTS


def main():
    root = Path("results/science-benchmark").resolve()
    geometries = json.loads((root / "report.json").read_text())
    results = []
    for record in geometries:
        if record["method"] != "GFN2-xTB" or record["case"] not in {
            "cis-H",
            "trans-2-Me",
        }:
            continue
        name = record["case"]
        start = time.perf_counter()
        with (
            (root / f"{name}-GFN2-ts.log").open("w") as log,
            contextlib.redirect_stdout(log),
        ):
            try:
                opt = OptTS(
                    common.xyz_to_atoms(record["tight_xyz"]),
                    calc=common.DefaultASECalculator(method="GFN2-xTB", accuracy=0.1),
                )
                ok = bool(opt.run())
                result = {
                    "case": name,
                    "method": "GFN2-xTB",
                    "converged": ok,
                    "barrier_ev": opt.barrier_ev,
                    "iterations": opt.iterations_used,
                    "failure_reason": opt.failure_reason,
                    "validation": opt.validation,
                    "connectivity": opt.connectivity,
                }
            except Exception as exc:
                result = {
                    "case": name,
                    "method": "GFN2-xTB",
                    "converged": False,
                    "error": str(exc),
                }
        result["seconds"] = time.perf_counter() - start
        results.append(result)
        (root / "ts-methods.json").write_text(
            json.dumps(results, indent=2, allow_nan=False)
        )
        print(
            f"{name}: converged={result['converged']}, {result['seconds']:.1f} s",
            flush=True,
        )


if __name__ == "__main__":
    main()
