# Scientific defaults and limitations

The application supports qualitative comparisons of structures and spectra
for first-year chemistry students. The [sensitivity benchmark](science-benchmark.md)
compares numerical settings and methods; it does not establish experimental
accuracy.

## Geometry and energy

- **GFN1-xTB with ALPB ethanol.** The parent trans minimum is nearly planar and
  lies below the sampled cis minimum in this model. The GFN2 comparison gives
  twisted trans minima and reverses this energy ordering in ALPB ethanol.
  This motivates the teaching default, not a general claim that GFN1 is superior.
- **Maximum force 0.002 eV/Å.** Ordinary minima, TS endpoints and downhill
  connectivity checks use the same criterion. Flexible substituents can still
  relax appreciably at the looser 0.01 eV/Å threshold.
- **xTB numerical accuracy 0.1.** Optimization and final energy reporting use
  the same setting so reported energy differences share numerical settings.
- **One deterministic starting conformation.** The calculation finds one local
  minimum. It does not establish a global minimum, a Boltzmann population or
  an ensemble spectrum.

The [TS calculation](transition-state.md) follows one electronic energy surface.
It omits transitions between surfaces, including singlet/triplet pathways.
Its electronic energy barrier does not predict a cis-isomer lifetime.

## UV/Vis spectra

- **INDO/S–CIS, COSMO ethanol, MAXCI=800.** The configuration cutoff balances
  runtime and qualitative comparison. Increasing it to 2000 changes peaks and
  intensities, so 800 is not established as converged; 2000 is not an exact
  reference either. Result metadata records the cutoff.
- **Gaussian standard deviation 0.15 eV.** This illustrative width is not fitted
  to experiment. Sticks retain calculated oscillator strengths.
- **WRTCI=100**, expanded if needed to cover the plot plus four Gaussian standard
  deviations. A coverage flag identifies insufficient output. This checks
  transition output, not convergence of the configuration expansion.
- **Visible-range plot scaling.** Only visible sticks and the displayed broadened
  curve set the vertical scale.

The [solution-color comparison](solution-color-validation.md) documents spectral
errors that prevent quantitative color predictions. No empirical correction is
applied.

## Verification

`pixi run -e dev test-science` checks parent planarity and cis/trans energy
ordering. `pixi run -e dev test-ts` checks real minimum-to-TS calculations.
Both are opt-in. Application and numerical unit tests run with
`pixi run -e dev test-web`; frontend tests use `node --test tests/*.cjs`.
Offline benchmark scripts do not run in the web application or default tests.
