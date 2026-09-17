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

The preview runs at `http://127.0.0.1:3000/`. Changes to Markdown, templates,
CSS, JavaScript and figures trigger a rebuild and browser reload. Use
`pixi run -e dev site --port 3002` if that port is occupied. A failed rebuild
prints its error and keeps the last successful preview available. Restart the
preview after editing the Python builder itself.

For website-only work, `pixi run -e site site` uses a lightweight environment
without the chemistry dependencies. Build and verify production output with:

```sh
pixi run --locked -e site test-site
pixi run --locked -e site build-site
```

The output in `site/_build/` is a self-contained static site. All internal URLs
are relative, so the same build works at a domain root or a GitHub project path.
The GitHub Actions workflow tests and builds pull requests and deploys `main`
to GitHub Pages. Pages must be configured to deploy through GitHub Actions.

Regenerate the SVG teaching figures with:

```sh
pixi run -e dev python figures/scripts/generate.py
```

Each figure also has an independently runnable source; see [figure sources](../figures/README.md)
for individual regeneration and optional PNG export. Review generated images before committing them. The [repository
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
task contains a title and a `.protocol-output` paragraph. On all three pages,
`details.task` provides an individually collapsible task inside a plain page section. The task panel
shows only the current calculation step, with a separate, initially collapsed “Weitere Schritte” section pointing to the
next page or final protocol submission. Collapsible sections start closed and retain the student’s chosen state.
Tasks use short German action titles that are unique across all three pages.
Descriptive English task IDs (for example, `task-compare-configurations`) remain
stable internal identifiers, independent of page order and title wording. Links
point to explicit, stable labels in `site/theory.md` on GitHub Pages.

The editable download is
`src/achprak/web/static/materials/protokollvorlage.docx`. It is included in Python
packages and served locally under `static/materials/`, including through the Hub
proxy. Students complete the document outside the app and submit through ILIAS.
Do not put completed student protocols in this directory.

During the current task review, leave the Word download unchanged.
The generator reads titles from `details.task > summary` and uses descriptive task IDs.
Its task references and answer fields follow the current exercise structure.
Review all titles, required outputs and answer fields together before regenerating the download.
At that point, run `python scripts/build_protocol.py` in an authoring
environment with `python-docx` and `lxml`. The script reuses the app's task titles
and required outputs; it supplies the corresponding answer fields and tables.
Update those tables when the required quantities or molecules change. Regeneration
replaces the DOCX, so make maintained changes in the script and task HTML.
Render the resulting Word document and inspect every page before release.
Document-authoring dependencies are not required to run the app.

`site/assets/teaching.css` uses the app's navy, blue, neutral colours and typography.
`scripts/build_site.py` renders the three Markdown pages through `site/template.html`.
The page order and navigation labels are defined in the builder's `PAGES` constant.
Python-Markdown handles tables, fenced code, explicit heading IDs and Markdown
inside HTML elements marked `markdown="1"`. Use native `<details>`/`<summary>`
for optional reading, `<aside class="callout">` for essential caveats, and
`<figure>`/`<figcaption>` for attributed illustrations. Preserve the stable
heading IDs referenced by the app. Assets referenced in the content are copied
into the build automatically; missing files fail the build.

Dollar-delimited equations are parsed by Arithmatex and converted to native
MathML at build time by latex2mathml. Modern browsers render them without a CDN
or client-side math library. Navigation, equations and disclosures work without
JavaScript; the small local script adds full-text search.
The build creates a local search index and Markdown source downloads. The live
reload script is injected only by the preview server, never into published files.
Developer dependencies are resolved in `pixi.lock`; CI uses that same environment.

Keep task titles, units, terminology and the protocol's answer fields aligned.

## Substituent display labels

Student-facing text and structure labels use CH₃, OCH₃ and N(CH₃)₂.
The API, saved settings and benchmark case identifiers retain `Me`, `OMe`
and `NMe2` for compatibility. Translate these identifiers at display time;
do not change chemistry inputs or stored identifiers to Unicode labels.
