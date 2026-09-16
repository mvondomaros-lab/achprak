# Development

Use `pixi run -e dev web` for development. New jobs load worker changes;
reload the browser for frontend changes and restart for server changes.

```sh
pixi run -e web web --port 8001 --max-jobs 2 --job-timeout 600
```

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

See [repository contents and local files](repository-layout.md) for Git
tracking decisions, generated assets and PyCharm exclusions.

Student-facing text uses German and addresses students as **Sie**.
See [AGENTS.md](../AGENTS.md) for audience and scientific terminology conventions.
For application installation and Hub integration, see the
[deployment guide](../deploy/README.md).
