# Scientific defaults and limitations

AChPrak supports qualitative comparisons of azobenzene structures, electronic
energy barriers and absorption spectra. It uses approximate electronic-structure
methods so students can run calculations interactively. The [settings
benchmark](science-benchmark.md) measures sensitivity to numerical and method
choices; it does not establish agreement with experiment.

## Geometry and electronic energy

**GFN1-xTB** is the approximate electronic-structure method used for geometry
optimization and energies. **ALPB** (analytical linearized Poisson–Boltzmann)
represents ethanol as a surrounding medium rather than as individual solvent
molecules. Every reported energy difference must compare structures calculated
with the same method and settings.

For unsubstituted azobenzene, the sampled trans minimum is nearly planar and lower
in energy than the sampled cis minimum with this model. The GFN2-xTB comparison
gives twisted trans minima and reverses that energy ordering in ALPB ethanol. This
is the reason for the teaching default; it does not establish that GFN1-xTB is
generally more accurate.

The geometry search stops when the largest atomic force is below **0.002 eV/Å**
(electronvolts per ångström). The same threshold is used for ordinary minima,
reaction-path endpoints and downhill connectivity checks. Flexible substituents
can still move appreciably at the looser 0.01 eV/Å threshold.

The xTB numerical accuracy parameter is **0.1** for both optimization and final
energy reporting. This is a program setting, not a claim of 0.1 eV accuracy.

One reproducible starting conformation is generated for each input. The resulting
minimum is local. This procedure does not determine the global minimum,
equilibrium conformer populations or a spectrum averaged over those populations.

## Transition states and barriers

The [transition-state search](transition-state.md) follows one electronic energy
surface. It does not model transitions between electronic states, including
singlet/triplet pathways or the light-driven switching process.

The **electronic energy barrier, ΔE‡**, is the transition-state energy minus the
energy of the calculation's source minimum. It excludes zero-point, thermal and
entropic corrections. It is neither an Arrhenius activation energy nor a Gibbs
energy of activation and cannot by itself predict a cis-isomer lifetime.

## UV/Vis absorption spectra

**INDO/S–CIS** combines a spectroscopic semiempirical model with configuration
interaction using single excitations. The latter describes excited states by
combining configurations in which one electron is promoted from an occupied to an
unoccupied orbital. **COSMO** (conductor-like screening model) represents the
electrostatic effect of ethanol; its dielectric constant is set to 24.3.

The following settings control different parts of the calculation:

| Setting | Role | Practical consequence |
| --- | --- | --- |
| `MAXCI=800` | Limits the configurations included in the excited-state calculation. | Balances cost and qualitative comparison. Increasing it to 2000 changes bands and intensities; neither cutoff is an exact reference. |
| `WRTCI=100`, increased if needed | Controls how many calculated states MOPAC prints. | Ensures transitions extend beyond the plotted range. It does not enlarge the configuration expansion. |
| Gaussian standard deviation **0.15 eV** | Replaces each discrete transition with a smooth band. | Illustrates a broadened spectrum; the width is not fitted to experiment. |

An **oscillator strength** is a dimensionless measure of transition intensity. The
stick spectrum retains those strengths. The displayed energy range, including its
broadened curve and transition sticks, determines the plot's vertical scale; this
is not a concentration calibration.

Output coverage is checked up to four Gaussian standard deviations beyond the
plot's upper energy limit. Insufficient output is flagged. Passing this check
means the printed transitions cover the required range, not that the excited-state
calculation is converged with respect to its configuration cutoff.

The [experimental spectral comparison](solution-color-validation.md) documents
band-position and intensity errors that prevent quantitative solution-color
predictions. The application applies no empirical correction.

## Checking an installation or a change

The [development guide](development.md) separates routine software tests from
optional calculations using the chemistry programs. Use `test-science` to check
the parent molecule's planarity and cis/trans energy ordering, and `test-ts` for
selected minimum-to-transition-state calculations. These checks detect changes in
model behavior; they are not a validation against experiment.
