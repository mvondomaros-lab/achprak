# Exhaustive azobenzene TS screening

See the [completed screening results](ts-screening-results.md) for coverage,
regression outcomes, and measured runtime.

Run the symmetry-reduced screen with up to four workers:

```sh
MPLCONFIGDIR=/tmp/achprak-mpl pixi run -e dev python scripts/screen_ts.py --scope both-rings --unique --workers 4 --output results/ts-screen-unique
```

The six historical non-hydrogen groups fixed in `scripts/screen_ts.py` are combined at
all available ring positions, with one or two substituents in total. Mixed
and repeated substituents are included. Independent reflection of each ring
and exchange of the two rings identify equivalent substitution patterns;
cis and trans remain distinct. The enumeration is checked against RDKit
canonical isomeric SMILES without generating 3D geometries.

| Substitution pattern | Distinct molecules | Cis/trans starting cases |
| --- | ---: | ---: |
| One substituent | 18 | 36 |
| Two substituents on the same ring | 186 | 372 |
| One substituent on each ring | 171 | 342 |
| Total | 375 | 750 |

`--unique` chooses one representative of each symmetry class, preferring an
already completed calculation. The manifest lists its equivalent labels.
Existing geometries retain their original atom order and case ID. Previously
observed failures remain regression fixtures even if another embedding of
the same substitution pattern succeeds. Symmetry reduction identifies
chemical substitution patterns; it does not sample every conformer or prove
that different embeddings lead to the same minimum or transition structure.

The earlier first-ring enumeration contained 780 labeled cis/trans cases before
symmetry reduction. Completed results are retained under `results/ts-screen/`; the expanded
screen uses `results/ts-screen-unique/`, with reused-record hashes in
`reuse-provenance.json`. This enumeration covers the six historical groups
(Me, NMe2, CF3, OMe, F, SO2CF3), not the revised course menu with CN and NO2,
not all possible chemical substituents.

Each case uses deterministic seed 42 and follows the application's XYZ
serialization and 500-step minimum optimization. The historical screen used up to
four deterministic seeds, with 1500 optimization steps per attempt. The
original 120-degree CNN seed runs first. On failure, the search tries reversed
rotation and a more open 135-degree seed. A final 150-degree seed is tried
only if those attempts fail. Endpoint-preparation failures and
downhill branches that change the bond graph try the open seed first.
The first attempt retains FIRE for band relaxation. Alternative attempts use
L-BFGS, with the same maximum step size and force thresholds; this avoids
repeating a stalled FIRE path without changing successful first attempts.
Bond perception uses RDKit's extended Hueckel overlap method. Distance-only
perception incorrectly added an S–N bond to a 2.135 Å intramolecular contact in
the trans-2-SO2CF3-6-NMe2 source minimum, causing a false connectivity failure.
The overlap method preserves its template connectivity without dropping the
bond-preservation check. See the [RDKit API documentation](https://rdkit.org/docs/source/rdkit.Chem.rdDetermineBonds.html).
All seed constraints are removed before validation.
The reported iteration count includes failed attempts, and individual attempt
outcomes are retained. Successful original searches do not run extra seeds. The
method is GFN1-xTB with ALPB ethanol, using the production force and numerical
accuracy settings. A successful search must satisfy the production all-atom
frequency and downhill cis/trans connectivity checks. Numerical success does
not establish experimental barrier accuracy or identify the globally lowest
barrier.

Reported barriers are electronic energy differences ΔE‡ in electronvolts (eV),
relative to the source minimum, without zero-point or thermal corrections.
The optimized minima are local minima; the screen does not establish that
they are the global minima.

Results and logs are written per case under the chosen output (git-ignored).
A completed JSON record is written atomically, so interrupted cases can be
rerun. Repeating the command skips completed records, including failures.
Use a **new output directory** after changing the optimizer, to keep baseline
and modified-code results separate. Do not run overlapping selections into
the same output directory concurrently.

An archived implementation can be screened with `--implementation PATH`.
This allows a baseline screen to continue while fixes are developed; its
source checksum is recorded in the manifest. Such baseline results describe
the archived implementation, not the current optimizer.

```sh
# Inspect progress without launching calculations.
pixi run -e dev python scripts/screen_ts.py --scope both-rings --unique --output results/ts-screen-unique --summarize
# Preserve every observed failure in the opt-in regression suite.
pixi run -e dev python scripts/screen_ts.py --output results/ts-screen-unique --collect-failures
# Recheck a single deterministic template in a separate output directory.
pixi run -e dev python scripts/screen_ts.py --case trans-r1-2-NMe2_r1-6-CF3 --output results/ts-recheck
# Run all saved failures and the existing web-workflow regressions.
pixi run -e dev test-ts
```

Failure fixtures are stored in `tests/data/ts_failures/`. TS failures retain the
exact source minimum; earlier failures retain the generated starting geometry
when available. Existing fixtures are never overwritten by later runs.
The regression tests are marked `ts_optimization` and remain disabled in
default test runs. A source-minimum failure is reported separately from a TS
failure, since no valid TS search can start in that case.

## Comparing reliability and cost

The optional `scripts/benchmark_ts_strategy.py` compares the current bounded
current policy with a direct 150°/L-BFGS attempt, using identical
saved source minima. Every candidate must produce a fully optimized path. It
includes every saved failure and 12 passing controls balanced by configuration
and substitution pattern, using a stable hash of the case ID. It records calculator calls and wall time, including
frequency and connectivity validation. Comparisons default to one worker;
`--workers` allows up to four, with one numerical thread per worker.

The optional `lbfgs_neb` candidate changes only the optimizer used to relax the band, keeping
the maximum step size and all convergence criteria. It uses no line search.

The optional dynamic candidate (`--strategy dynamic_neb`) uses a uniform
0.05 eV/Å band-force threshold and no
distance-dependent tolerance scaling. It skips updates to converged images
and reactivates them if needed. It is an experimental cost comparison; it
does not change the production optimizer. See the
[dynamic NEB paper](https://doi.org/10.1021/acs.jctc.9b00633).

```sh
MPLCONFIGDIR=/tmp/achprak-mpl pixi run -e dev python scripts/benchmark_ts_strategy.py --screen results/ts-screen-unique
```

### Direct 150°/L-BFGS comparison

Use `--strategy current --strategy open150_lbfgs` to compare the production
policy with a 150°/L-BFGS seed attempted directly once. The recorded comparison
used the former four-attempt policy; rerunning now uses the two-attempt policy. The
candidate retains the 1,500-step budget, full path optimization, and all
frequency/connectivity checks. It has no further fallback.

The benchmark includes every saved failure and 12 passing controls, balanced
across cis/trans and mono-, same-ring di-, and cross-ring disubstitution.
Selection within each stratum uses a stable case-ID hash. Each worker runs
both methods consecutively for one molecule, alternating their order across
molecules. Elapsed time, process CPU time, and calculator calls are recorded;
calculator calls provide a comparison less sensitive to worker contention.
Failures must be reported separately from speed ratios for successful pairs.

```sh
MPLCONFIGDIR=/tmp/achprak-mpl pixi run -e dev python scripts/benchmark_ts_strategy.py --screen results/ts-screen-unique --output results/ts-open150-comparison --workers 4 --strategy current --strategy open150_lbfgs
```

## Current retry limit

All TS searches now use at most two attempts: the original 120°/FIRE path,
then a failure-directed reversed 120° or open 135° path with L-BFGS.
The third attempt and 150° fallback have been removed. Full optimized paths,
frequency validation, and cis/trans connectivity checks remain required.

The web menu is H, Me, OMe, NMe2, CF3, CN, and NO2, with at most two non-H
substituents across both rings for TS searches. Saved regression fixtures using
removed groups have been deleted. CN and NO2 have opt-in web workflow cases;
the historical exhaustive screen above does not cover these groups.

Minimum refinement within a TS attempt uses internal-coordinate Sella followed
by at most 25 Cartesian BFGS steps at the same 0.002 eV/Å force tolerance.
This finishing stage addresses residual forces observed for trans-2-CN without
adding another seed or increasing the 1500-step total per attempt. The exact
failing CN minimum is retained as a regression fixture. Replacing minimum
refinement entirely with Cartesian BFGS or Cartesian Sella regressed retained
crowded cases and was discarded.

Validation after simplification: the complete 19-case chemistry run passed 18
cases and exposed a CN playback defect (Sella dummy atom in trajectory frames).
After filtering helper atoms from playback, the focused CN web rerun passed.
All 19 chemistry cases therefore have passing checks across the complete run
and focused rerun; the full suite was not repeated after this playback-only fix.
The fast suite passed 141 tests with 21 opt-in cases skipped. Logs and diagnostics
are retained in `results/ts-simplified-menu/`. This is regression coverage, not
an exhaustive screen of the revised menu.
