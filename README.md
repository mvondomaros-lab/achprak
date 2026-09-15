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

The German-language interface includes structure generation, 2D/3D viewing,
properties, minimum/transition-state optimization, trajectory and vibration
playback, UV/Vis spectra, the exercise tasks, unit conversion, and image/data
exports. Structures are built only from the predefined cis/trans configurations
and substituent choices; names are generated automatically. XYZ import and custom
name input are not supported. XYZ export remains available. Select a structure once and carry it through the calculation steps.
Long calculations run in isolated worker processes and can be cancelled. During
minimum and transition-state searches, the 3D geometry, energy and maximum force
update live at accepted optimizer steps (the browser polls every 400 ms). A live
energy chart shows ΔE relative to the first step, with absolute energies on hover.
Every geometry and energy is retained in the result, including runs that finish
between polls. Short runs automatically replay for up to three seconds, explicitly
labeled as playback, with a skip button; reduced-motion preferences disable this
automatic replay. The energy chart remains available afterward. Clicking a point in the energy chart selects its structure. Play/Pause and
the playback mode selector sit beside the chart; there is no separate slider.
Arrow keys, Home and End step through frames when the chart has focus. Play resumes from the paused
or manually selected step, stops at the final frame, and never loops. Pressing
Play at the final frame starts a new playback from the beginning. For transition states,
a mode selector switches the chart controls between the reaction path, search geometries,
and the imaginary TS mode. Starting structures are labeled “Startstruktur”. The structure picker searches and wraps full molecule names; result names retain only
the current optimization type.

Step 1 offers only starting structures, with a “Strukturformel / 3D-Startstruktur”
toggle. It defaults to 2D and remembers the chosen view while switching
structures or panels. The 3D view allows rotation and zoom and identifies the
geometry as not yet energy-optimized. Returning
there from a calculated result selects its source starting structure; returning
to step 2 restores the result. Explicitly choosing or creating a different
starting structure makes that structure the next selection in step 2. Minima
and transition states remain selectable in step 2's 3D view.
The structure picker also offers “Alle Strukturen löschen” to clear all
structures and their spectra in the current session after confirmation. This
includes entries hidden by the current panel or search filter and is unavailable
while a calculation is active.

TS searches require a converged minimum. A relaxed CNNC torsion scan seeds a
13-image path toward the opposite cis/trans isomer, preserving atom identity and
rotating the complete fragment. CNN angles are guided to 120° only during seed
preparation. The opposite endpoint is then freely minimized. Regular minimum
searches, opposite endpoints, and connectivity checks all use a final maximum
atomic force of 0.002 eV/Å and the same xTB accuracy setting (0.1).
ASE FIRE relaxes
two unconstrained NEB halves against a provisionally refined central saddle seed.
This prevents early corner cutting from removing the barrier. The full band is
then released for climbing-image NEB. Both stages use 0.1 eV/Å² springs;
stronger springs stalled the trans-2-Me half-path relaxation. Free Sella saddle
refinement follows, using a full Cartesian Hessian and a 0.005 eV/Å force threshold.
Candidates with additional imaginary modes are refined to 0.001 eV/Å within the
shared iteration budget, then their Hessian is recalculated. This resolves soft
torsions without weakening mode validation. The central seed
is approached in internal coordinates and finished in Cartesian coordinates;
final saddle refinement also uses Cartesian coordinates to handle nearly linear
CNN angles. Both endpoints use
the same GFN1-xTB/ALPB ethanol
model as the band. The full search has a shared
1500-iteration budget, plus the server's wall-time limit.

The live chart shows the evolving band's energy against normalized Cartesian
path length, not optimization time. The live 3D preview follows a moving image
of the active half-band, then the climbing image during CI-NEB. The plot highlights
the displayed image. On completion, clickable energy points and the
single-pass Play control can show the reaction path, optimization history, or
imaginary vibration. Both endpoint geometries and their energies are retained
in the result; the other endpoint is available as the final path image.

A full all-atom finite-difference Hessian (0.01 Å displacement) checks the saddle.
Rigid translations and rotations are projected out; exactly one imaginary
internal frequency above 20 cm⁻¹ is required. Smaller negatives are tolerated as
numerical noise. Displacement by ±0.15 Å maximum atom motion along the unstable
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
a TS. The vibration is illustrative, not dynamics. Barriers are electronic energy
differences, not free-energy barriers. See [ASE's NEB documentation](https://docs.ase-lib.org/ase/neb.html).

For development, use `pixi run -e dev web`.
New jobs load changes to the chemistry workers automatically. Reload the browser
after HTML/CSS/JS changes; restart the process for changes to the server itself
(this clears in-memory sessions). Optional command-line settings:

```sh
pixi run -e web web --port 8001 --max-jobs 2 --job-timeout 600
```

Results are held per browser session until server restart or 24 hours of
inactivity. Download XYZ coordinates, PNG images and SVG/CSV spectra for your
protocol. A page reload reconnects to any running calculation.

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

The webapp replaces the notebook interface. Notebook widgets, clipboard helpers,
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
is feature-detected; this browser does not provide a WebMCP validation context.

The web interface has three steps: create a structure, optimize its geometry,
and calculate a UV/Vis spectrum. Starting structures and optimization results
include energy, CNNC angle and ring distance automatically. Exercise numbers
remain aligned with the original lab handout. Method details are expandable;
student-facing explanations distinguish search iterations from a reaction path
and from physical motion.
