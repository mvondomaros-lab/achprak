# Azobenzene TS screening

The opt-in screen in `scripts/screen_ts.py` enumerates one or two substituents
from the course menu (Me, OMe, NMe2, CF3, CN, NO2) across both rings.
Independent ring reflections and ring exchange identify equivalent substitution
patterns; cis and trans remain distinct. Canonical RDKit isomeric SMILES check
the enumeration without generating 3D geometries.

| Substitution pattern | Distinct patterns | Cis/trans starting cases |
| --- | ---: | ---: |
| One substituent | 18 | 36 |
| Two substituents on the same ring | 186 | 372 |
| One substituent on each ring | 171 | 342 |
| Total | 375 | 750 |

These are enumeration counts, not successful-calculation counts. The current
menu and optimizer do not have a completed exhaustive validation recorded here.
The regression suite covers selected templates and exact failing geometries.
Symmetry reduction does not sample every conformer or establish that equivalent
starting labels reach the same minimum or transition structure.

## Run and resume

```sh
MPLCONFIGDIR=/tmp/achprak-mpl pixi run -e dev python scripts/screen_ts.py --scope both-rings --unique --workers 4 --output results/ts-course-screen
# Inspect saved results without launching calculations:
pixi run -e dev python scripts/screen_ts.py --scope both-rings --unique --output results/ts-course-screen --summarize
# Collect exact failing geometries as opt-in regression fixtures:
pixi run -e dev python scripts/screen_ts.py --output results/ts-course-screen --collect-failures
# Recheck one template separately:
pixi run -e dev python scripts/screen_ts.py --case trans-r1-2-NMe2_r1-6-CF3 --output results/ts-recheck
```

Each case uses seed 42, the application's XYZ serialization and a 500-step
minimum optimization. The TS search uses the production two-attempt policy:
120°/FIRE first, then reversed 120° or open 135°/L-BFGS according to the failure.
Each attempt has a shared 1,500-step budget. Full path, frequency and downhill
connectivity checks are required. See [the method](transition-state.md).

Results and logs are written per case under the git-ignored output directory.
JSON records are written atomically. Repeating the command skips completed
records, including failures. `--unique` prefers a completed representative and
records equivalent labels without changing atom order or case IDs.
Use a new output directory when code or packages change. Do not run overlapping
selections into the same directory concurrently. Manifests record source hashes,
package versions and the selected cases.

`--implementation PATH` loads a separate `transition_state.py` for controlled
optimizer comparisons; its source hash is included in the manifest.

## Regression coverage

```sh
pixi run -e dev test-ts
```

`tests/test_web.py` covers deterministic cis/trans parent templates and selected
Me, NMe2, CF3, CN and NO2 derivatives through the web worker.
`tests/test_ts_screen.py` runs the exact geometries in `tests/data/ts_failures/`.
Source-minimum failures are distinguished from TS failures. Collected fixtures
are never overwritten by later runs, even if another conformer succeeds.
All real chemistry regressions remain disabled in default test runs.

A successful calculation establishes numerical convergence and downhill
cis/trans connectivity for the chosen model. It does not establish a globally
lowest barrier, an IRC, or agreement with experiment. Barriers are electronic
energy differences ΔE‡ relative to the source minimum, without zero-point,
thermal or entropic corrections.

## Compare reliability and cost

`scripts/benchmark_ts_strategy.py` compares production searches with experimental
band optimizers and seed choices using saved source minima. It includes saved
failures and passing controls selected by a stable case-ID hash, balanced by
configuration and substitution pattern. Each candidate must produce a full path
and pass frequency and connectivity checks.

```sh
pixi run -e dev python scripts/benchmark_ts_strategy.py --screen results/ts-course-screen
pixi run -e dev python scripts/benchmark_ts_strategy.py --screen results/ts-course-screen --output results/ts-open150-comparison --workers 4 --strategy current --strategy open150_lbfgs
```

`open150_lbfgs` makes one direct 150°/L-BFGS attempt with a 1,500-step budget.
`lbfgs_neb` changes the band optimizer. `dynamic_neb` skips updates to converged
images with a uniform 0.05 eV/Å band-force threshold. These are offline
comparisons, not additional production retries.

Workers run paired methods consecutively and alternate their order across
molecules. Reports include wall time, CPU time and calculator calls. Compare
failures separately from speed ratios for successful pairs; calculator calls
are less sensitive to worker contention than elapsed time.
