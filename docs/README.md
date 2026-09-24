# Technical documentation

These pages support contributors, scientists, and educators maintaining AChPrak
or assessing its calculations. Student-facing explanations are on the
[practicum website](https://mvondomaros-lab.github.io/achprak/).

## Current methods

- [Scientific defaults and limitations](science-decisions.md): model choices,
  settings, and their rationale.
- [Transition-structure calculation](transition-state.md): search procedure and
  numerical acceptance criteria.
- [Solution-color model](solution-color.md): spectral conversion, assumptions,
  and data provenance.

## Recorded evaluations

- [JupyterHub load test](hub-load-test-2026-09-24.md): 12 concurrent student
  workflows, host load, and a local single-user comparison.
- [Scientific settings benchmark](science-benchmark.md): sensitivity to numerical
  settings, methods, and starting structures.
- [Experimental spectral comparison](solution-color-validation.md): a recorded
  parent-azobenzene comparison and instructions for repeating it.

Reports describe the calculations and implementation recorded at the time, not
automatic verification of later versions. Software checks establish program
behavior; numerical checks assess the chosen model's convergence and sensitivity;
experimental comparisons assess agreement with measurements.

## Development and operation

- [Development](development.md): setup, tests, website editing, and protocol generation.
- [Transition-structure screening](ts-screening.md): batch calculations, failure
  collection, and regression coverage.
- [Repository layout](repository-layout.md): source files, generated assets, and local outputs.
- [Project README](../README.md): local installation and startup.
- [Deployment guide](../deploy/README.md): JupyterHub hosting.
