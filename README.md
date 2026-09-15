# Practical Exercise: Introducing Theoretical Chemistry to First-Year Chemistry Students

> [!NOTE]
> This exercise is currently available in German only.

## Overview

The materials are available on GitHub Pages:

[![Docs](https://img.shields.io/badge/docs-github%20pages-blue)](https://mvondomaros-lab.github.io/achprak/)

## Web app

Install [Pixi](https://pixi.sh), clone this repository, then run:

```sh
pixi install -e web
pixi run -e web web
```

Open **http://127.0.0.1:8000/**. Python, RDKit, tblite, Sella and MOPAC are managed
by Pixi. The NGL browser viewer is bundled locally; no Node build or CDN is needed.

## Student workflow

The German-language interface has three steps:

1. **Create a starting structure.** Choose cis or trans and the substituents.
   View the structure as a 2D formula or a rotatable 3D model. The view selector
   defaults to 2D and remembers the choice when switching structures or steps.
2. **Optimize a structure.** Search for a local minimum or, from an optimized
   minimum, a transition state. Inspect the geometry, energy, CNNC dihedral angle
   and distance between the ring centres.
3. **Calculate a UV/Vis spectrum.** Use an optimized minimum to predict electronic
   excitation energies and relative absorption strengths.

Each step offers an expandable **Was passiert im Hintergrund?** explanation:
what the method does, how to read the result, and what its limits are.
The exercise tasks and unit converter are available throughout the app.

Step 1 lists only starting structures. Returning there from a result selects its
source starting structure; returning to step 2 restores the result. Explicitly
choosing or creating a different starting structure carries that selection into
step 2. The structure picker groups related molecules and searches their names
and formulas. **Alle Strukturen löschen** clears all structures and spectra in
that browser session after confirmation, including entries hidden by a search
or step filter. Clearing is unavailable while a calculation is active.

Structures are generated from predefined configurations and substituents.
Names are assigned automatically; custom names and XYZ imports are not supported.
Students can export coordinates, images and spectra for their lab reports.

### Calculation progress and playback

Calculations run in isolated worker processes and can be cancelled. During
optimization, the viewer shows accepted geometries and the energy chart updates
as the browser polls for progress. All recorded geometries and energies remain
available, including those calculated between polls.

The chart distinguishes optimization steps from the reaction path. Clicking a
point selects its geometry. Arrow keys, Home and End select frames when the
chart has focus. **Abspielen / Pause** is in the viewer toolbar; the playback
mode selector is beside the chart. Playback resumes at the selected frame and
stops at the end. Starting playback at the last frame restarts it.
For a transition state, students can choose the reaction path, search history,
or the illustrated unstable mode.

Short calculations may finish before students see any live progress. These runs
replay for up to three seconds, with a clear playback label and a skip button.
Reduced-motion preferences disable this automatic replay. Neither optimization
playback nor the illustrated unstable mode represents molecular dynamics.

## Terminology and scientific scope

Use **transition state** (German **Übergangszustand**, abbreviation **TS**) as the
main teaching term. Use **transition structure** (**Übergangsstruktur**) when
specifically distinguishing the calculated saddle-point geometry from the wider
transition-state concept. The student theory page explains this distinction,
following IUPAC's definitions of [transition state](https://goldbook.iupac.org/terms/view/T06468)
and [transition structure](https://goldbook.iupac.org/terms/view/T06471).

Call the calculated difference **electronic energy barrier**, $\Delta E^\ddagger$.
It is not generally the Arrhenius activation energy or a Gibbs energy of activation.
Student-facing text uses German, addresses students as **Sie**, and explains
technical terms on first use. Developer documentation and code identifiers use
English. See [AGENTS.md](AGENTS.md) for the audience and language conventions.

### Transition-state search

TS searches require a converged minimum. A relaxed CNNC torsion scan seeds a
13-image path toward the opposite cis/trans isomer, preserving atom identity and
rotating the complete fragment. CNN angles are guided to 120° only during seed
preparation. The opposite endpoint is then freely minimized. Regular minimum
searches, opposite endpoints, and connectivity checks all use a final maximum
atomic force of 0.002 eV/Å and the same xTB accuracy setting (0.1).
ASE FIRE relaxes two unconstrained NEB halves against a provisionally refined central saddle seed.
This prevents early corner cutting from removing the barrier. The full band is
then released for climbing-image NEB. Both stages use 0.1 eV/Å² springs;
stronger springs stalled the trans-2-Me half-path relaxation. Free Sella saddle
refinement follows, using a full Cartesian Hessian and a 0.005 eV/Å force threshold.
Candidates with additional imaginary modes are refined to 0.001 eV/Å within the
shared iteration budget, then their Hessian is recalculated. This resolves soft
torsions without weakening mode validation. The central seed is approached in internal coordinates and finished in Cartesian coordinates;
final saddle refinement also uses Cartesian coordinates to handle nearly linear
CNN angles. Both endpoints and the band use GFN1-xTB with ALPB ethanol.
The full search shares a 1500-iteration budget and the server's wall-time limit.

The live chart shows the evolving band's energy against normalized Cartesian
path length, not optimization time. The live 3D preview follows a moving image
of the active half-band, then the climbing image during CI-NEB. The plot highlights
the displayed image. On completion, clickable energy points and the
single-pass Play control can show the reaction path, optimization history, or
imaginary vibration. Both endpoint geometries and their energies are retained
in the result; the other endpoint is available as the final path image.

A full all-atom finite-difference Hessian (0.01 Å displacement) checks the saddle.
Rigid translations and rotations are projected out; exactly one imaginary
internal frequency with magnitude above 20 cm⁻¹ is required. Smaller negative frequencies are tolerated by this numerical criterion;
they are not proof of additional physical instabilities. Displacement by ±0.15 Å maximum atom motion along the unstable
mode, followed by unconstrained minimization, must reach one cis and one trans
minimum with the original atom-mapped bond graph preserved. For this comparison,
copies of both band endpoints and the downhill minima are optimized to 0.002 eV/Å
to resolve soft torsions. Polishing takes place after the TS search and preserves
the original band and its energy reference. These actual downhill
minima (XYZ, energy, isomer) are retained separately. Matching to the polished
endpoint references additionally uses aligned RMSD <0.35 Å and energy difference <0.05 eV.
A different endpoint conformer is explicitly reported; isomer connectivity does
not establish an exact conformer match. This is a numerical downhill connectivity
check, **not an IRC** or a proof of the globally lowest barrier. Failed band, saddle,
mode or cis/trans connectivity checks leave an unconfirmed search state.
Only a force-converged saddle passing both mode and connectivity checks is labeled
a TS. The animation illustrates the unstable mode; it is not a periodic vibration or
a dynamics simulation. Barriers are electronic energy differences, not free-energy
barriers. See [ASE's NEB documentation](https://docs.ase-lib.org/ase/neb.html).

## Development and session lifetime

For development, use `pixi run -e dev web`.
New jobs load changes to the chemistry workers automatically. Reload the browser
after HTML/CSS/JS changes; restart the process for changes to the server itself
(this clears in-memory sessions). Optional command-line settings:

```sh
pixi run -e web web --port 8001 --max-jobs 2 --job-timeout 600
```

Results are held per browser session until server restart or 24 hours of
inactivity. Download XYZ coordinates, PNG images and SVG/CSV spectra for your
lab report. A page reload reconnects to any running calculation.

## Multiple users / self-hosted server

See [deploy/README.md](deploy/README.md) for the included JupyterHub configuration:
standard Unix accounts via PAM, one app instance per Unix user, authenticated
proxying, and a private Unix socket for each app. The optional `web-hub` Pixi
environment contains the server dependencies. Local development needs no Hub.

## Teaching materials

The theory pages remain in `site/`. Regenerate their figures without Jupyter:

```sh
pixi run -e dev python figures/scripts/figures.py
```

The web app replaces the notebook interface. Notebook widgets, clipboard helpers,
and the `local`, `hub`, and `lserver` environments have been removed. Use `web`
for local operation, `dev` for development, or `web-hub` for shared deployment.

## Verification

```sh
pixi run -e dev test-web
# Dedicated real TS regression set (run whenever investigating a TS failure):
pixi run -e dev test-ts
# One case while debugging; rerun the full set before finishing:
pixi run -e dev test-ts -k trans-2-Me
# Also run real minimum, UV/Vis and transition-state calculations:
ACHPRAK_CHEMISTRY_TESTS=1 pixi run -e dev test-web
# Frontend polling and short-run replay regressions (Node is test-only):
node --test tests/test_web_progress.cjs
```

The TS regression set is skipped by default. It starts from deterministic template
geometries and exercises the real web worker, minimum optimization, path search,
saddle modes and downhill connectivity. Cases cover cis/trans azobenzene,
cis/trans 2-Me, trans 2-NMe2 and trans 4-NMe2-4′-CF3. Each case retains its input,
optimized minimum and TS result in `ts-result.json` under pytest's temporary
directory, including the search history and failure reason. Add new failing
molecules to this set and run the full `test-ts` set when investigating or fixing
a TS search failure; normal `test-web` runs do not enable it. The broader
`ACHPRAK_CHEMISTRY_TESTS=1` run includes this set as well.

Local validation on macOS included the complete chemistry workflow (including
60 transition-state vibration frames), API session isolation, cancellation and
timeouts, and the standalone proxy with a `/user/test/` prefix and private Unix
socket. NGL rendering, optimization playback, 2D structures and spectra were also
checked in Safari. Linux PAM login and actual switching between Unix accounts
still need a deployment test on the target server. The optional WebMCP interface
is feature-detected and needs separate verification in a supporting browser.
