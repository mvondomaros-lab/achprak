"""Linux self-hosting: PAM login → per-Unix-user proxy → private app socket.

Run with the Pixi web-hub environment; see README.md for installation.
"""

import os
from pathlib import Path
import sys

c = get_config()  # noqa: F821 -- supplied by JupyterHub/traitlets

c.JupyterHub.bind_url = "http://127.0.0.1:8000"
c.JupyterHub.authenticator_class = "jupyterhub.auth.PAMAuthenticator"
# Restrict access to existing members of this Unix group; no accounts are created.
c.PAMAuthenticator.allowed_groups = {os.environ.get("ACHPRAK_UNIX_GROUP", "achprak")}
c.JupyterHub.spawner_class = "jupyterhub.spawner.LocalProcessSpawner"

# JupyterHub switches UID before starting this proxy. The actual application
# listens on a socket inside the proxy's private directory, not on a public port.
c.Spawner.cmd = [str(Path(sys.executable).with_name("jupyter-standaloneproxy"))]
c.Spawner.args = [
    "--unix-socket=True",
    "--timeout=60",
    "--",
    sys.executable,
    "-m",
    "achprak.web",
    "--unix-socket={unix_socket}",
    "--cookie-path={base_url}",
    "--max-jobs=1",
    "--job-timeout=600",
    "--secure-cookie",
]
c.Spawner.default_url = "/"
c.Spawner.environment = {
    "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""),
    "MPLBACKEND": "Agg",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
}
c.Spawner.start_timeout = 120
c.Spawner.http_timeout = 90
c.JupyterHub.concurrent_spawn_limit = 10
