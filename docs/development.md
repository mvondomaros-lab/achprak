# Development and verification

This guide covers changes to the application and teaching materials. For ordinary
local use, see the [project README](../README.md); for shared hosting, see the
[deployment guide](../deploy/README.md). The [repository layout](repository-layout.md)
describes source directories and which generated files belong in version control.

## Development setup

Run commands from the repository root. Pixi's `dev` environment contains the
application and development tools; dependencies are resolved in `pixi.lock`.

```sh
pixi install --locked -e dev
pixi run --locked -e dev web
```

Open `http://127.0.0.1:8000/`. Reload the browser after changing browser code and
restart the application after changing server code. Calculation code runs in
separate worker processes; newly submitted jobs load changes to that code.

To use a different port and limit the instance to two concurrent calculations,
each with a 600-second timeout:

```sh
pixi run -e dev web --port 8001 --max-jobs 2 --job-timeout 600
```

## Running checks

### Routine checks

```sh
pixi run -e dev test-web
node --test tests/*.cjs
```

These check the Python application and numerical utilities, and browser-side
logic, respectively. Node.js must be installed separately; it is not needed to
run the application. Inspect changed interfaces in a browser as well. Changes to
Hub integration also need a login test on a real Hub.

### Chemistry regression tests

These longer-running calculations are excluded from routine runs and are run
explicitly:

| Command | Purpose |
| --- | --- |
| `pixi run -e dev test-ts` | Real minimum-to-transition-structure calculations and saved failure cases. |
| `pixi run -e dev test-science` | The parent molecule's planarity and cis/trans energy ordering in the model. |
| `ACHPRAK_CHEMISTRY_TESTS=1 pixi run -e dev test-web` | Additional chemistry workflow checks. |

For a reported transition-structure search failure, add a reproducible regression
case and run the complete `test-ts` suite when verifying the fix. During debugging,
`pixi run -e dev test-ts -k trans-2-Me` selects matching test names.

Tests retain structures and search diagnostics in pytest's temporary directory.
See the [screening guide](ts-screening.md) for broader coverage and collecting
exact starting structures. These checks assess numerical behavior within the
model, not agreement with experiment.

## Editing the website and figures

Student-facing material is German, addresses students as **Sie**, and assumes
first-year chemistry knowledge without prior theoretical chemistry. Developer
documentation and code identifiers are English. See the
[scientific documentation](README.md) for the calculation definitions and their
interpretation.

The fundamentals live in `site/`; exercise instructions live in the app. Keep
conceptual explanations on the website and implementation-specific method details
in the app's optional help.

### Preview and build

```sh
pixi run -e dev site
```

The preview runs at `http://127.0.0.1:3000/` and rebuilds and reloads after changes
to content, styles, scripts, or figures. Use `--port 3002` if needed. A failed
rebuild prints its error and leaves the last successful preview available.
Restart the preview after changing the Python builder itself.

For website-only work, use the lightweight `site` environment:

```sh
pixi run --locked -e site site
pixi run --locked -e site test-site
pixi run --locked -e site build-site
```

Production output goes to `site/_build/`. Relative URLs support both domain-root
and project-path hosting. GitHub Actions tests and builds pull requests and
deploys `main`; GitHub Pages must be configured to deploy through Actions.

### Website sources

| Source | Purpose |
| --- | --- |
| `site/theory/*.md` | Fundamentals chapters. |
| `scripts/build_site.py` | Builder; `PAGES` defines page order and navigation labels. |
| `site/template.html` | Page template. |
| `site/assets/teaching.css` | Website styles. |
| `src/achprak/web/static/header.css` | Shared app/site header styles and `--page-inset`; copied by the site builder. |

Use source-relative Markdown links. The builder supports tables, fenced code,
explicit heading IDs, and Markdown inside HTML marked `markdown="1"`.
Use `<details>`/`<summary>` for optional reading and `<figure>`/`<figcaption>`
for illustrations. Dollar-delimited equations become native MathML at build
time. Referenced assets are copied automatically; missing files fail the build.

### Figures

```sh
pixi run -e dev python figures/scripts/generate.py
```

This regenerates the published SVGs. Each figure also has an independently
runnable source. See [figure sources](../figures/README.md) for individual exports
and typography conventions. Inspect changed figures at their published display
sizes before committing the source and generated SVG together.

## Updating tasks and the protocol

The task source is `src/achprak/web/static/guide.html`. Each `details.task` has a
stable ID, a title in `summary`, and required deliverables in a `.protocol-output`
paragraph. `scripts/build_protocol.py` reads those titles and deliverables and
adds the protocol's answer fields and tables.

When changing an exercise:

1. Update its instructions and required deliverables in `guide.html`.
2. Update the corresponding answer fields and tables in `scripts/build_protocol.py`
   when quantities, molecules, or expected responses change. Check that the
   website's learning goals still match the exercises.
3. Regenerate the DOCX if its titles, deliverables, or answer fields changed.
   Make maintained edits in the HTML and generator, not directly in the Word file.
4. Check that task wording, units, terminology, and protocol fields agree, and
   inspect the document layout before release.

For generation, activate a separate Python authoring environment with
`python-docx` and `lxml` installed, then run from the repository root:

```sh
python scripts/build_protocol.py
```

The script replaces `src/achprak/web/static/materials/protokollvorlage.docx`.
This file is bundled with the application and served under `static/materials/`,
including through the Hub proxy. Commit the regenerated template with its source
changes; keep completed student protocols outside the repository.

For layout verification, open the generated DOCX in Microsoft Word or LibreOffice
Writer and export it to PDF. Inspect every page for clipped text, broken tables,
missing symbols, and awkward page breaks; correct the generator and repeat if
needed. The repository does not bundle a document renderer. Keep the PDF local;
the published download remains the editable DOCX. Document-authoring tools are
not application dependencies.

## Compatibility and source conventions

- Keep descriptive task IDs stable when changing titles or page order: the
  protocol generator uses them to identify exercises.
- Preserve chapter heading IDs referenced by the app and the legacy anchors in
  `site/theory.md`, which forward older `/theory/#…` links to the current chapters.
- Student-facing substituent labels use CH₃, OCH₃, and N(CH₃)₂. The API, saved
  settings, and benchmark identifiers retain `Me`, `OMe`, and `NMe2`. Translate
  these at display time rather than changing stored identifiers or chemistry inputs.
