# Azobenzene TS screening results

## Coverage and outcome

The exhaustive screen covers the six supported substituents (Me, NMe2, CF3,
OMe, F, SO2CF3), with one or two substituents in total across either ring.
Independent ring reflections and exchange of the two rings reduce 3,300
labeled cis/trans cases to **750 distinct starting cases** (375 substitution
patterns). Enumeration was independently checked against canonical RDKit
isomeric SMILES.

| Starting cases | Count |
| --- | ---: |
| Monosubstituted | 36 |
| Two substituents on one ring | 372 |
| One substituent on each ring | 342 |
| Baseline searches passed | 725 |
| Baseline searches failed | 25 |
| Validated after fixes | **750** |
| Unresolved | **0** |

Thirty exact failing geometries are retained in the opt-in regression suite:
25 failed representatives and five previously observed, symmetry-equivalent
conformers. Coverage combines the retained baseline first-attempt successes
with the final regression results; all 750 calculations were not repeated
from scratch after each fix. Successful first attempts keep their original
numerical optimization settings.

## Search changes

Every successful search calculates the full optimized, 13-image reaction path,
then validates the refined saddle using all-atom frequencies and unconstrained
cis/trans downhill connectivity. No TS-only shortcut is used.

The bounded strategy retains the original 120° seed with FIRE first. Failed
searches try reversed rotation and a 135° seed with L-BFGS band relaxation;
endpoint-preparation or bond-connectivity failures prioritize the open seed.
A final 150° seed is tried only if those attempts fail. Each attempt has a
1,500-step budget shared across its stages. Total reported work includes all
attempts. Force and frequency acceptance criteria were not weakened.

A four-case full-path pilot found uniform L-BFGS successful in 4/4 cases,
compared with 3/4 for the earlier FIRE policy and dynamic NEB. Dynamic NEB
was slower on all four pilot cases. L-BFGS was not uniformly faster, so the
production policy retains FIRE for the first attempt. The additional 150°
seed resolved a crowded cross-ring SO2CF3 pair that stalled both optimizers
at 135°, including experiments with longer band-relaxation stages.

The last regression failure was a bond-perception error: a 2.135 Å S···N
contact in trans-2-SO2CF3-6-NMe2 was interpreted as a covalent bond by the
distance-based method. RDKit's extended Hueckel overlap method restores the
intended connectivity. An audit of 4,526 saved geometries found no assignment
errors or template-connectivity mismatches with this method; the only graph
change was the problematic source minimum. The corrected case passed on its
first attempt in a focused 114-second calculation. See the
[RDKit bond-perception API](https://rdkit.org/docs/source/rdkit.Chem.rdDetermineBonds.html).

## Verification and cost

- Complete `pixi run -e dev test-ts -n 4`: **36 passed** in 40 min 44 s.
- Default Python suite: **41 passed, 38 skipped**; expensive chemistry stays opt-in.
- Selection-pane JavaScript tests: **28 passed**; nested badges were replaced
  with plain labels and the selected-item checkmark.
- All 750 source minima retained their intended cis/trans identity.
- Final saved-geometry, endpoint-connectivity, and UI-serialization audit:
  **755 checked, zero failures** (750 representatives plus five extra conformers).

The 30 failure regressions needed one attempt in one case, two in 23 cases,
three in five cases, and four in one case. The longest final regression took
650 seconds under four-worker contention. Difficult retries can therefore
exceed the web server's default 600-second job limit; configure a larger
`--job-timeout` when running them through the web application. This limit
remains separate from the per-attempt step budget.

These results apply to deterministic generated conformers and local minima
with GFN1-xTB and ALPB ethanol. They do not establish a universally convergent
method, the globally lowest reaction barrier, or experimental accuracy.
Reported ΔE‡ values are electronic energy differences, without zero-point,
thermal, or entropic corrections. The downhill test confirms cis/trans
connectivity; it is not a mass-weighted IRC calculation.

## Local result files

- [Validated coverage summary](../results/ts-screen-unique/validated-summary.json)
- [Validated per-case table](../results/ts-screen-unique/validated-summary.csv)
- [Original baseline summary](../results/ts-screen-unique/summary.json)
- [Final regression report](../results/ts-screen-unique/regression-junit.xml)
- [Final geometry audit](../results/ts-screen-unique/audit-final.json)
- [Bond-perception audit](../results/ts-screen-unique/audit-hueckel-final.json)

Raw results are local, git-ignored artifacts. Source hashes, package versions,
exact input geometries, and symmetry-equivalent labels are retained alongside
the results. See [screening instructions](ts-screening.md) to reproduce the run.
