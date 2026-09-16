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
| `pixi run -e dev test-ts` | Run selected real minimum-to-transition-state calculations and saved failure cases. |
| `pixi run -e dev test-science` | Check the parent molecule's planarity and cis/trans energy ordering in the model. |
| `ACHPRAK_CHEMISTRY_TESTS=1 pixi run -e dev test-web` | Include the additional chemistry workflow checks enabled by this environment variable. |

A **regression case** is a fixed input whose result is checked after code changes.
Whenever investigating or fixing a transition-state search failure, add a
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
