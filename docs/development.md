# Development and verification

Use this guide when adapting the application or teaching materials, or checking a
code change. For ordinary local use, follow the [project README](../README.md).
For shared hosting, use the [deployment guide](../deploy/README.md).

Run commands from the repository root. Pixi's `dev` environment contains the
application plus development tools; installing it downloads the required packages
without changing a separately managed JupyterHub.

```sh
pixi install --locked -e dev
pixi run --locked -e dev web
```

Open `http://127.0.0.1:8000/`. After changing browser code, reload the page. After
changing server code, restart the application. Calculation code runs in separate
worker processes; newly submitted jobs load changes to that code.

To change the port or calculation limits:

```sh
pixi run -e dev web --port 8001 --max-jobs 2 --job-timeout 600
```

This example allows two concurrent calculations in that instance and limits each
to 600 seconds of elapsed time. Open port 8001 in the browser for this example.

## Teaching materials

The German student documentation lives in `site/`. Preview it locally with:

```sh
pixi run -e dev site
```

Regenerate teaching figures with:

```sh
pixi run -e dev python figures/scripts/figures.py
```

Review generated images before committing them. The [repository
layout](repository-layout.md) explains which generated files belong in version
control.

## Routine tests

```sh
pixi run -e dev test-web
node --test tests/*.cjs
```

The first command checks the Python application and numerical utilities. The
second checks browser-side logic and requires Node.js to be installed separately.
Node.js is a development tool here; it is not needed for local application use.
These checks do not replace a browser inspection or a login test on a real Hub.

## Optional chemistry calculations

These commands run calculations that can take substantially longer. They are
excluded from the default suite and must be requested explicitly.

| Command | Purpose |
| --- | --- |
| `pixi run -e dev test-ts` | Run selected real minimum-to-transition-structure calculations and saved failure cases. |
| `pixi run -e dev test-science` | Check the parent molecule's planarity and cis/trans energy ordering in the model. |
| `ACHPRAK_CHEMISTRY_TESTS=1 pixi run -e dev test-web` | Include the additional chemistry workflow checks enabled by this environment variable. |

A **regression case** is a fixed input whose result is checked after code changes.
Whenever investigating or fixing a transition-structure search failure, add a
reproducible case for the reported molecule and run the complete `test-ts` suite
before finishing. During debugging, a command such as `pixi run -e dev test-ts -k
trans-2-Me` selects matching test names only; it does not replace the full run.
Report any remaining failures.

Tests retain geometries and search diagnostics in pytest's temporary directory.
The [screening guide](ts-screening.md) describes broader molecule coverage and how
to collect exact starting geometries. Passing these checks establishes software or
numerical behavior, not agreement with experiment.

## Text and terminology

Student-facing text is German and addresses students as **Sie**. Technical
identifiers and developer documentation are English. Follow
[AGENTS.md](../AGENTS.md) for scientific terminology, audience conventions and
required verification.

## Tasks and protocol template

The app bundles its tasks in `src/achprak/web/static/guide.html`. Each
task contains a title and a `.protocol-output` paragraph. On pages 01 and 02,
`details.task` provides an individually collapsible task inside a plain page section;
page 03 still uses `section.task` inside a collapsible page section. The task panel
shows only the current calculation step, with a separate, initially collapsed “Weitere Schritte” section pointing to the
next page or final protocol submission. Collapsible sections start closed and retain the student’s chosen state.
Tasks use descriptive titles without visible task numbering.
Stable task IDs remain internal identifiers for the protocol generator. Links
point to explicit, stable labels in `site/theory.md` on GitHub Pages.

The editable download is
`src/achprak/web/static/materials/protokollvorlage.docx`. It is included in Python
packages and served locally under `static/materials/`, including through the Hub
proxy. Students complete the document outside the app and submit through ILIAS.
Do not put completed student protocols in this directory.

During the current task review, leave the Word template and its generator unchanged.
Synchronize all titles, required outputs and answer fields in one final pass.
Update the generator to read task titles from `details.task > summary` as well
as `section.task > h3`.
At that point, run `python scripts/build_protocol.py` in an authoring
environment with `python-docx` and `lxml`. The script reuses the app's task titles
and required outputs; it supplies the corresponding answer fields and tables.
Update those tables when the required quantities or molecules change. Regeneration
replaces the DOCX, so make maintained changes in the script and task HTML.
Render the resulting Word document and inspect every page before release.
Document-authoring dependencies are not required to run the app.

`site/teaching.css` uses the app's navy, blue, neutral colours and typography,
with the same palette in the protocol's tables. MyST includes it through
[`site.options.style`](https://mystmd.org/guide/website-style).
Preview with the existing `site` task; verify the Pages build using
`cd site` followed by `BASE_URL=/achprak pixi run -e dev myst build --html`.
Keep task titles, units, terminology and the protocol's answer fields aligned.

## Substituent display labels

Student-facing text and structure labels use CH₃, OCH₃ and N(CH₃)₂.
The API, saved settings and benchmark case identifiers retain `Me`, `OMe`
and `NMe2` for compatibility. Translate these identifiers at display time;
do not change chemistry inputs or stored identifiers to Unicode labels.
