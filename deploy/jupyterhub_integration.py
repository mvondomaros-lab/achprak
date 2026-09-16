"""Load from an independently managed Hub's configuration; see README.md."""

import os
from pathlib import Path

c = get_config()  # noqa: F821 -- supplied by JupyterHub/traitlets

# This path belongs to the application, not the Python running the central Hub.
achprak_env = Path(os.environ.get("ACHPRAK_ENV", "/opt/achprak/.pixi/envs/web-hub"))
if not achprak_env.is_absolute():
    raise ValueError("ACHPRAK_ENV must be an absolute environment path")
achprak_bin = achprak_env / "bin"

# JupyterHub switches UID before starting this proxy. The actual application
# listens on a socket inside the proxy's private directory, not on a public port.
c.Spawner.cmd = [str(achprak_bin / "jupyter-standaloneproxy")]
c.Spawner.args = [
    "--unix-socket=True",
    "--timeout=60",
    "--",
    str(achprak_bin / "python"),
    "-m",
    "achprak.web",
    "--unix-socket={unix_socket}",
    "--cookie-path={base_url}",
    "--max-jobs=1",
    "--job-timeout=600",
    "--secure-cookie",
]
c.Spawner.default_url = "/"
c.Spawner.environment.update(
    {
        "PATH": str(achprak_bin) + os.pathsep + "/usr/local/bin:/usr/bin:/bin",
        # Personal pip installs must not override the locked app dependencies.
        # Inherited by the proxy, application and calculation workers.
        "PYTHONNOUSERSITE": "1",
        "MPLBACKEND": "Agg",
        "OMP_NUM_THREADS": "1",
        "OPENBLAS_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
    }
)
c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 90
