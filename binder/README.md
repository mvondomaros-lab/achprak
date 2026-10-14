# Binder

[![Launch Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mvondomaros-lab/photoswitchlab/main?urlpath=photoswitchlab%2F)

The first launch builds the environment; later launches can reuse it. Startup
and calculations can be slower than on a local computer. Sessions are temporary,
so export your results. Long calculations may reach Binder's
[runtime limits](https://mybinder.readthedocs.io/en/latest/about/user-guidelines.html).

## Development

The files in this directory install the locked Pixi `web` environment and launch
the app through Jupyter Server Proxy at `photoswitchlab/`. Use a commit SHA or
release tag in the launch link instead of `main` to share a fixed version.

For a local check, install Docker and [repo2docker](https://repo2docker.readthedocs.io/)
and run from the repository root on x86-64 Linux:

```sh
jupyter-repo2docker --image-name photoswitchlab-binder .
```

Open the printed URL, then navigate to `photoswitchlab/`. After configuration
changes, check structure generation, optimization, spectra, cancellation and
exports locally and in a live Binder session.
