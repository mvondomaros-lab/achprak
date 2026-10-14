# Binder

[![Launch Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mvondomaros-lab/photoswitchlab/main?urlpath=photoswitchlab%2F)

The first launch builds the environment; later launches can reuse it. Sessions
are temporary, so export results. Long calculations may reach Binder's
[runtime limits](https://mybinder.readthedocs.io/en/latest/about/user-guidelines.html).

## Development

This directory installs the locked Pixi `web` environment and launches the app
through Jupyter Server Proxy at `photoswitchlab/`. Use a commit SHA or release
tag instead of `main` to share a fixed version.

To test locally on macOS (including Apple Silicon) or x86-64 Linux, install and
start Docker. [repo2docker](https://repo2docker.readthedocs.io/) is included in
Pixi's `dev` environment. From the repository root:

```sh
pixi install --locked -e dev
```

Then build and run the Binder environment:

```sh
pixi run --locked -e dev jupyter-repo2docker \
    --Repo2Docker.platform=linux/amd64 \
    --image-name photoswitchlab-binder \
    .
```

The Linux x86-64 target matches Binder. On Apple Silicon, Docker uses emulation,
so builds and calculations can be slower.

Open the printed URL, then navigate to `photoswitchlab/`. After configuration
changes, verify calculations, cancellation and exports locally and on Binder.
