# Repository contents and local files

This guide is for educators and contributors who adapt the code or teaching
materials. Git is the version-control system used to share source files and review
changes. Files kept only on a local machine are not available to someone who
downloads a fresh checkout.

## Where to find things

| Directory or file | Contents |
| --- | --- |
| `src/achprak/` | Chemistry calculations and the browser application. |
| `site/` | German student guide and teaching pages. |
| `docs/` | Scientific explanations, evaluation reports and contributor guides. |
| `deploy/` | Integration with an independently managed JupyterHub. |
| `tests/` | Automated checks and selected fixed molecular inputs. |
| `scripts/` | Explicitly run screening, benchmark and validation tools. |
| `figures/` | Figure sources and selected rendered teaching images. |
| `pyproject.toml`, `pixi.lock` | Requested dependencies and the exact resolved package versions. |

## Files to keep in version control

- Application code, tests, scripts, deployment configuration and documentation.
- `pyproject.toml` and `pixi.lock`: the environment definition and resolved
  dependencies needed to reproduce installations.
- `tests/data/ts_failures/`: selected, exact geometries for reproducible
  regression tests, which check whether behavior changes after a code edit. These are test inputs, not disposable run output.
- `figures/drawings/` and `figures/commons/`: editable artwork and attributed
  source images, including the PowerPoint source for the dihedral illustration.
- Published figures referenced by `site/theory.md`, and the app's bundled
  `static/substituent-effects.png`. These rendered assets are intentional:
  a checkout can build the site and run the app without regenerating artwork.
- Bundled browser libraries, color tables and their licenses under
  `src/achprak/web/static/vendor/`. Offline operation depends on these files.

The root `.gitignore` lists which generated figures are deliberately kept in Git.
Generate previews with `pixi run -e dev python figures/scripts/figures.py`. Review
changed images before committing them. To update the app illustration, copy the
generated `figures/outputs/substituent-effects.png` to its bundled static path.

## Files to keep local

`results/` contains raw calculations, logs, downloaded validation data and
benchmark reports. Commit selected summaries in `docs/` and regression inputs in
`tests/data/`, not entire calculation directories.

The `.gitignore` rules exclude installed environments (`.pixi/`, `.venv/`), Python
bytecode (cached compiled code), package metadata, generated build output,
test-coverage reports and caches used by code-checking tools. Ignore `.idea/`,
notebook caches and OS metadata. `site/.gitignore` excludes the MyST `_build/`
directory.

Unpublished figure exports under `figures/outputs/` are ignored. This includes
`dihedral.png`, `profile-no-labels.png` and the duplicate generated
`substituent-effects.png`; they may remain locally but are not Git inputs. Do not
ignore all PNG, JSON, XYZ or lock files: those formats also hold required assets
and reproducible inputs.

<details>
<summary>Optional PyCharm editor configuration</summary>

Keep `.idea/` local. Use the repository as the content root, `src/` as a source
root and `tests/` as a test root. Select `.pixi/envs/dev/bin/python` as the
project interpreter. Exclude:

- `.pixi/`, `.venv/` and `results/`;
- `site/_build/`, `build/`, `dist/`, `htmlcov/` and `src/achprak.egg-info/`;
- `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.ipynb_checkpoints/` and
  `.virtual_documents/`;
- `src/achprak/web/static/vendor/`, to avoid indexing minified third-party code.

Keep application code, scripts, documentation, artwork and regression fixtures
available to the IDE. IDE exclusion only controls indexing; it does not decide
whether a file belongs in Git. The bundled vendor files remain tracked.

</details>
