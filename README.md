# AChPrak: theoretical chemistry practical

A German-language web application for first-year chemistry students.
[Student documentation](https://mvondomaros-lab.github.io/achprak/)
introduces the calculations and exercises.

## Run locally

Install [Pixi](https://pixi.sh), clone this repository, then run:

```sh
pixi install -e web
pixi run -e web web
```

Open **http://127.0.0.1:8000/**. Pixi manages Python and the chemistry tools.
Browser libraries are bundled locally; no Node build or CDN is needed.

## Student workflow

1. Generate a cis or trans starting structure with H, Me, OMe, NMe2, CF3,
   CN or NO2 at each ring site. Inspect its 2D formula or 3D geometry.
2. Optimize a local minimum, then optionally search for a transition state
   (TS). TS searches require a converged minimum with at most two non-H
   substituents across both rings.
3. Calculate an INDO/S–CIS UV/Vis spectrum for an optimized minimum.
   The solution-color preview uses a relative optical-density control;
   it is not calibrated to concentration or measured solution colors.

Starting structures use deterministic ETKDG embedding and bounded MMFF
preparation. These construction restraints do not enter the xTB optimization.
Equivalent ring positions can produce different starting conformers.
A converged minimum is local; it need not be the global minimum.

The structure picker groups related results. Step 1 shows starting structures;
step 2 shows their calculation results. Calculation status is displayed
separately from configuration and substitution labels. Students can export
structure images and spectra as PNG. Each step includes an expandable
explanation of its method and limitations.

Calculations run in isolated, cancellable worker processes. Accepted geometries
and energies are retained for optimization playback; TS results include a
clickable reaction path. Neither playback represents molecular dynamics.
Completed calculations load their result directly; playback starts on request.

Results belong to a browser session and expire after 24 hours of inactivity
or a server restart. Reloading the page reconnects to a running calculation.
**Alle Strukturen löschen** clears the session's structures and spectra after
confirmation and is unavailable during calculations.

## Scientific settings

Geometry optimization and energies use GFN1-xTB with ALPB ethanol, numerical
accuracy 0.1, and a minimum force threshold of 0.002 eV/Å. TS searches allow
at most two attempts of 1,500 steps each, subject to the server's wall-time
limit. Confirmation requires a converged saddle, one imaginary internal
frequency above the numerical magnitude threshold, and downhill connectivity
to cis and trans minima. The electronic energy barrier ΔE‡ excludes zero-point,
thermal and entropic corrections; it is not a Gibbs energy of activation.

Spectra use INDO/S–CIS with COSMO ethanol, MAXCI=800 and Gaussian standard
deviation 0.15 eV. The width is illustrative. Output coverage is checked beyond
the plotted window, but this does not establish configuration convergence.

- [Transition-state method and validation](docs/transition-state.md)
- [Scientific defaults and limitations](docs/science-decisions.md)
- [Sensitivity benchmark](docs/science-benchmark.md)
- [Solution-color model](docs/solution-color.md)
- [TS screening and regression coverage](docs/ts-screening.md)

Student-facing text uses German and addresses students as **Sie**.
See [AGENTS.md](AGENTS.md) for scientific terminology and audience conventions.

## Development and deployment

Use `pixi run -e dev web` for development. New jobs load worker changes;
reload the browser for frontend changes and restart for server changes.

```sh
pixi run -e web web --port 8001 --max-jobs 2 --job-timeout 600
```

[Deployment instructions](deploy/README.md) cover integration with an independently
managed JupyterHub. The optional `web-hub` environment provides authenticated
proxying and one app instance per user; the central Hub has its own environment.

Teaching materials live in `site/`. Preview with `pixi run -e dev site`.
Regenerate figures with `pixi run -e dev python figures/scripts/figures.py`.

## Verification

```sh
pixi run -e dev test-web
node --test tests/*.cjs
# Opt-in real chemistry regressions:
pixi run -e dev test-ts
pixi run -e dev test-science
ACHPRAK_CHEMISTRY_TESTS=1 pixi run -e dev test-web
```

Expensive chemistry tests are disabled by default. Run the complete `test-ts`
set whenever investigating a TS search failure; add a deterministic fixture
for each newly failing molecule. A focused run such as
`pixi run -e dev test-ts -k trans-2-Me` is useful during debugging.
Tests retain geometry and search diagnostics in pytest's temporary directory.
Node is needed only for frontend tests.

See [repository contents and local files](docs/repository-layout.md) for Git
tracking decisions, generated assets and PyCharm exclusions.
