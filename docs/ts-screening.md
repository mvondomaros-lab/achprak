# Transition-structure screening and regression coverage

This page describes how to assess whether the transition-structure (TS) search
completes for a set of course molecules. A screen runs the same workflow over many
structures. A regression test repeats a selected calculation to detect changes
after modifying the software. Neither measures agreement with experiment.

The optional [`screen_ts.py`](../scripts/screen_ts.py) screen enumerates one or
two substituents from the course menu across both rings: methyl (CH₃), methoxy
(OCH₃), dimethylamino (N(CH₃)₂), trifluoromethyl (CF3), cyano (CN) and nitro (NO2).
Independent ring reflections and ring exchange identify equivalent substitution
patterns; cis and trans remain distinct. RDKit checks the enumeration using
canonical isomeric SMILES: standardized text representations of molecular
connectivity and stereochemistry. This check does not require three-dimensional
structures.

| Substitution pattern | Distinct patterns | Cis/trans starting cases |
| --- | ---: | ---: |
| One substituent | 18 | 36 |
| Two substituents on the same ring | 186 | 372 |
| One substituent on each ring | 171 | 342 |
| Total | 375 | 750 |

These are enumeration counts, not successful-calculation counts. The current menu
and optimizer do not have a completed exhaustive validation recorded here. The
regression suite covers selected templates and exact failing structures. Symmetry
reduction does not sample every conformer or establish that equivalent starting
labels reach the same minimum or transition structure.

## Run and resume

Run commands from the repository root after installing the `dev` environment with
`pixi install --locked -e dev`. Four workers means up to four concurrent
calculations; reduce this number if memory is limited. The complete screen can be
expensive, so begin with a single case when checking a new installation.

Case identifiers encode the input rather than a molecule name. For example,
`trans-r1-2-NMe2_r1-6-CF3` means a trans input with N(CH₃)₂ at position 2 and CF3 at
position 6 on ring 1. `r2` denotes ring 2. A seed such as 42 makes the initial
structure generation reproducible.

```sh
# Check one template first:
pixi run -e dev python scripts/screen_ts.py --case trans-r1-2-NMe2_r1-6-CF3 --output results/ts-recheck
# Run the complete screen:
MPLCONFIGDIR=/tmp/achprak-mpl pixi run -e dev python scripts/screen_ts.py --scope both-rings --unique --workers 4 --output results/ts-course-screen
# Inspect saved results without launching calculations:
pixi run -e dev python scripts/screen_ts.py --scope both-rings --unique --output results/ts-course-screen --summarize
# Collect exact failing structures as opt-in regression fixtures:
pixi run -e dev python scripts/screen_ts.py --output results/ts-course-screen --collect-failures
```

Each case uses seed 42, the application's XYZ coordinate-file representation and a
500-step minimum optimization. The TS search uses the production attempt policy
and acceptance checks described in [the method](transition-state.md).

Results and logs are written per case under the git-ignored output directory.
Each JSON record is written as a complete file before replacing its destination,
so an interrupted write does not leave a
partially written record. Repeating the command skips completed records, including
failures. `--unique` prefers a completed representative and records equivalent
labels without changing atom order or case IDs. Use a new output directory when
code or packages change. Do not run overlapping selections into the same directory
concurrently. A manifest records checksums identifying the source files, package
versions and the selected cases, so results can be traced to their calculation
setup.

`--implementation PATH` loads a separate `transition_state.py` for controlled
optimizer comparisons; a checksum identifying that source file is included in the
manifest.

## Regression coverage

```sh
pixi run -e dev test-ts
```

`tests/test_web.py` covers deterministic cis/trans parent templates and selected
CH₃, N(CH₃)₂, CF3, CN and NO2 derivatives through the web worker.
`tests/test_ts_screen.py` runs the exact structures in `tests/data/ts_failures/`.
Source-minimum failures are distinguished from TS failures. Collected fixtures are
never overwritten by later runs, even if another conformer succeeds. All real
chemistry regressions remain disabled in default test runs.

Interpret a successful result using the method page's
[acceptance criteria](transition-state.md#what-an-accepted-result-establishes).

## Compare reliability and cost

`scripts/benchmark_ts_strategy.py` compares production searches with experimental
band optimizers and seed choices using saved source minima. It includes saved
failures and passing controls selected reproducibly from their case identifiers,
balanced by configuration and substitution pattern. Each candidate must produce a
full path and pass frequency and connectivity checks.

```sh
pixi run -e dev python scripts/benchmark_ts_strategy.py --screen results/ts-course-screen
pixi run -e dev python scripts/benchmark_ts_strategy.py --screen results/ts-course-screen --output results/ts-open150-comparison --workers 4 --strategy current --strategy open150_lbfgs
```

`open150_lbfgs` makes one direct 150°/L-BFGS attempt with a 1,500-step budget.
`lbfgs_neb` changes the band optimizer. `dynamic_neb` skips updates to converged
images with a uniform 0.05 eV/Å band-force threshold. These comparisons run
separately from the application and do not add retries to the student workflow.

Workers run paired methods consecutively and alternate their order across
molecules. Reports include elapsed wall-clock time, processor time (CPU time), and
the number of energy/force evaluations (calculator calls). Compare failures
separately from speed ratios for successful pairs; calculator calls are less
sensitive to competition between simultaneous calculations for hardware resources
than elapsed time.
