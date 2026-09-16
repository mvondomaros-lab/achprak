# Scientific and teaching documentation

These notes are for scientists and educators who want to understand the
calculations, assess their suitability for a course, or maintain an installation.
They assume basic chemistry but do not require experience with the software's
optimization algorithms.

For local installation, start with the [project README](../README.md). For
classroom hosting, use the [JupyterHub deployment guide](../deploy/README.md). The
[student guide](https://mvondomaros-lab.github.io/achprak/) is in German.

## Choose a topic

| Question | Documentation |
| --- | --- |
| What does the model calculate, and what can students conclude? | [Scientific defaults and limitations](science-decisions.md) |
| How is a transition state found and checked? | [Transition-state calculation](transition-state.md) |
| How much do numerical settings and starting geometries affect results? | [Settings benchmark](science-benchmark.md) |
| What does the displayed solution color represent? | [Color model](solution-color.md) |
| How does the spectrum compare with a measurement? | [Experimental spectral comparison](solution-color-validation.md) |
| Which molecules have been checked, and how can coverage be extended? | [Transition-state screening](ts-screening.md) |
| How do I change the application or run tests? | [Development](development.md) |
| Which files should be kept when sharing changes? | [Repository layout](repository-layout.md) |

## Distinguish three kinds of evidence

- **Software checks** establish that a feature behaves as intended, for example
  that a spectrum can be parsed or two browser sessions keep separate results.
- **Numerical checks** assess convergence and sensitivity within the chosen
  model, for example the response to a tighter geometry threshold.
- **Experimental comparisons** assess agreement with measurements under stated
  conditions. Passing software and numerical checks does not establish this
  agreement.

A generated starting structure is an input geometry. Optimization searches from
that input for a local minimum; it does not identify the global minimum by itself.
A confirmed transition state passes the numerical checks described in its method
page, rather than an experimental validation of the reaction model.

Technical pages use decimal points. Energies are given in electronvolts (eV) per
molecule or kilojoules per mole (kJ mol⁻¹); 1 eV per molecule corresponds to about
96.485 kJ mol⁻¹. Lengths use ångströms (Å; 1 Å = 0.1 nm). A force threshold in
eV/Å limits the remaining atomic forces, not the error in a measured quantity.
