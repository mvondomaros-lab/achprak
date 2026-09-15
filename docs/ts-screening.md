# Exhaustive azobenzene TS screening

Run the first-ring screen explicitly:

```sh
MPLCONFIGDIR=/tmp/achprak-mpl pixi run -e dev python scripts/screen_ts.py --scope first-ring --workers 8
```

The six non-hydrogen groups in `Template.substituent_smiles` are combined at
all five first-ring positions. There are 30 monosubstituted and 360
disubstituted labeled templates, each tested from both cis and trans: **780
calculations**. Mixed substituents and repeated substituents are included.
The second ring remains unsubstituted. Symmetry-related labels are retained
because RDKit embedding and subsequent local optimization can select different
conformations. This is exhaustive over the supported labels, not over all
chemical substituents or conformations.

Each case uses deterministic seed 42 and follows the application's XYZ
serialization and 500-step minimum optimization. The TS search tries up to
three deterministic seeds, with 1500 optimization steps per attempt. The
original 120-degree CNN seed runs first. On failure, the search tries reversed
rotation and a more open 135-degree seed. Endpoint-preparation failures and
downhill branches that change the bond graph try the open seed first.
All seed constraints are removed before validation.
The reported iteration count includes failed attempts, and individual attempt
outcomes are retained. Successful original searches do not run extra seeds. The
method is GFN1-xTB with ALPB ethanol, using the production force and numerical
accuracy settings. A successful search must satisfy the production all-atom
frequency and downhill cis/trans connectivity checks. Numerical success does
not establish experimental barrier accuracy or identify the globally lowest
barrier.

Results and logs are written per case under `results/ts-screen/` (git-ignored).
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
pixi run -e dev python scripts/screen_ts.py --summarize
# Preserve every observed failure in the opt-in regression suite.
pixi run -e dev python scripts/screen_ts.py --collect-failures
# Recheck a single deterministic template in a separate output directory.
pixi run -e dev python scripts/screen_ts.py --case trans-r1-2-SO2CF3 --output results/ts-recheck
# Run all saved failures and the existing web-workflow regressions.
pixi run -e dev test-ts
```

Failure fixtures are stored in `tests/data/ts_failures/`. TS failures retain the
exact source minimum; earlier failures retain the generated starting geometry
when available. Existing fixtures are never overwritten by later runs.
The regression tests are marked `ts_optimization` and remain disabled in
default test runs. A source-minimum failure is reported separately from a TS
failure, since no valid TS search can start in that case.
