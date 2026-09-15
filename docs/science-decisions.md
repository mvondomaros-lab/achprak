# Scientific defaults after the sensitivity benchmark

The audience is first-year chemistry students exploring structures and spectra
interactively. The numerical measurements are in [science-benchmark.md](science-benchmark.md).
They measure sensitivity and runtime, not accuracy against experiment.

## Adopted

- Gaussian standard deviation **0.15 eV**, previously 0.3 eV. This resolves more
  of the calculated band structure. It is an illustrative width, not an
  experimental fit. Sticks retain the calculated oscillator strengths.
- xTB numerical accuracy **0.1 for final energies as well as optimization**.
  The measured discrepancy was tiny; this change makes reported differences
  and TS barriers numerically consistent.
- **WRTCI=100**, with a larger output request if required to cover the plot
  plus four Gaussian standard deviations. MOPAC 23.2.4 produces 99 transitions
  for this request. A coverage flag and student-facing note identify spectra
  that do not cover the requested window. This verifies output coverage only,
  not convergence of the underlying configuration expansion.
- Plot scaling uses only visible sticks and the displayed broadened curve.
  Printing more transitions therefore cannot compress the visible spectrum
  merely because a stronger transition lies outside the plotted window.
- Explicit **INDO/S–CIS** naming and an optional explanation that the TS model
  omits transitions between electronic surfaces, including singlet/triplet
  pathways. The calculated barrier does not predict a cis-isomer lifetime.
- An opt-in scientific regression checks that default trans-azobenzene is
  nearly planar and has lower model energy than cis-azobenzene.

## Retained after testing

### GFN1-xTB with ALPB ethanol

GFN2-xTB is unsuitable as the replacement default in this workflow. Its parent
trans geometry has substantial ring twists, even after unconstrained Cartesian
refinement to 0.0001 eV/Å. The lower sampled trans minimum has ring twists of
approximately 18° and 21°. A deliberately planar starting geometry also relaxes
to a nonplanar local minimum. Full internal-mode Hessians have positive
frequencies for these refined geometries. This is not just a loose stopping
threshold. GFN1 approaches planarity under the same refinement.

GFN2 also places the sampled parent cis minimum below trans in ALPB ethanol;
GFN1 preserves the ordering needed for this exercise. Absolute total energies
were never compared across methods. Two GFN2 TS searches did pass the numerical
validation, illustrating why optimizer success alone cannot select a method.

This does not validate GFN1's quantitative barrier heights or establish that
it is generally superior to GFN2. The decision applies to this teaching model.

### Maximum force 0.002 eV/Å

The 0.01 eV/Å trial saves little time for the small molecules, while flexible
donor substituents continue to relax after reaching that threshold. Retaining
0.002 keeps the ordinary minimum, TS endpoints and connectivity checks on the
same criterion. The additional complexity of separate loose and tight workflows
is not justified by these measurements.

### MAXCI=800

Increasing to 2000 configurations changes calculated peaks and intensities, so
800 should not be described as converged. It also substantially increases
spectral runtime, especially for larger derivatives. For the interactive
qualitative exercise, retain 800 and record the cutoff in result metadata.
The benchmark keeps both calculations for review. A 2000-configuration run is
itself a comparison, not an exact reference; no empirical correction is applied.

### One deterministic starting conformation

Alternative embedding seeds were tested for flexible molecules. Keep the
single deterministic start for the primary workflow, together with the existing
explanation that only one local minimum is found. Two seeds cannot establish
a global minimum, a Boltzmann population, or an ensemble absorption spectrum.

## Verification

- `pixi run -e dev test-ts`: all six real chemistry cases passed.
- `pixi run -e dev test-science`: parent planarity and energy ordering passed.
- `pixi run -e dev test-web`: application and numerical unit tests passed.
- `node --test tests/test_web_progress.cjs`: all 23 frontend tests passed.
- A real INDO/S–CIS spectrum was generated through the application worker;
  output coverage was confirmed and the rendered plot was visually inspected.

All expensive chemistry regressions remain opt-in. Offline benchmark scripts
do not run as part of the web application or the default tests.
