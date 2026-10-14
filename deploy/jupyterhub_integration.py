"""Load from an independently managed Hub's configuration; see README.md."""

import os
from pathlib import Path

c = get_config()  # noqa: F821 -- supplied by JupyterHub/traitlets

# This path belongs to the application, not the Python running the central Hub.
default_env = Path("/opt/photoswitchlab/.pixi/envs/web-hub")
# Existing installations can keep their environment at its original location.
legacy_env = Path("/opt/achprak/.pixi/envs/web-hub")
if not default_env.exists() and legacy_env.exists():
    default_env = legacy_env
photoswitchlab_env = Path(
    os.environ.get(
        "PHOTOSWITCHLAB_ENV", os.environ.get("ACHPRAK_ENV", str(default_env))
    )
)
if not photoswitchlab_env.is_absolute():
    raise ValueError("PHOTOSWITCHLAB_ENV must be an absolute environment path")
photoswitchlab_bin = photoswitchlab_env / "bin"

# JupyterHub switches UID before starting this proxy. The actual application
# listens on a socket inside the proxy's private directory, not on a public port.
c.Spawner.cmd = [str(photoswitchlab_bin / "jupyter-standaloneproxy")]
c.Spawner.args = [
    "--unix-socket=True",
    "--timeout=60",
    "--",
    str(photoswitchlab_bin / "python"),
    "-m",
    "photoswitchlab.web",
    "--unix-socket={unix_socket}",
    "--cookie-path={base_url}",
    "--max-jobs=1",
    "--job-timeout=600",
    "--secure-cookie",
]
c.Spawner.default_url = "/"
c.Spawner.environment.update(
    {
        "PATH": str(photoswitchlab_bin) + os.pathsep + "/usr/local/bin:/usr/bin:/bin",
        # Personal pip installs must not override the locked app dependencies.
        # Inherited by the proxy, application and calculation workers.
        "PYTHONNOUSERSITE": "1",
        "PHOTOSWITCHLAB_COURSE": os.environ.get(
            "PHOTOSWITCHLAB_COURSE", os.environ.get("ACHPRAK_COURSE", "public")
        ),
        "MPLBACKEND": "Agg",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
)
c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 90
