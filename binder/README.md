# Binder

[![Launch Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mvondomaros-lab/photoswitchlab/main?urlpath=photoswitchlab%2F)

The first launch builds the environment; later launches can reuse it. Sessions
are temporary, so export results. Long calculations may reach Binder's
[runtime limits](https://mybinder.readthedocs.io/en/latest/about/user-guidelines.html).

## Development

This directory installs the locked Pixi `web` environment and launches the app
through Jupyter Server Proxy at `photoswitchlab/`. Use a commit SHA or release
tag instead of `main` to share a fixed version.

To test locally with Docker and [repo2docker](https://repo2docker.readthedocs.io/),
run from the repository root on x86-64 Linux:

```sh
jupyter-repo2docker --image-name photoswitchlab-binder .
```

Open the printed URL, then navigate to `photoswitchlab/`. After configuration
changes, verify calculations, cancellation and exports locally and on Binder.
