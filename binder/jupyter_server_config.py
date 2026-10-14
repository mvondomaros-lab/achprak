"""Start the locked PhotoSwitchLab environment on demand behind Binder's Jupyter server."""

import os
from pathlib import Path

c = get_config()  # noqa: F821 -- supplied by Jupyter/traitlets
repo_root = Path(os.environ["PHOTOSWITCHLAB_BINDER_ROOT"])
app_bin = repo_root / ".pixi/envs/web/bin"


def photoswitchlab_command(unix_socket, base_url):
    command = [
        str(app_bin / "python"),
        "-m",
        "photoswitchlab.web",
        f"--unix-socket={unix_socket}",
        f"--cookie-path={base_url.rstrip('/')}/photoswitchlab/",
        "--max-jobs=1",
        "--job-timeout=600",
    ]
    # Binder serves HTTPS; keep plain HTTP usable for local repo2docker checks.
    if os.environ.get("JUPYTERHUB_SERVICE_PREFIX"):
        command.append("--secure-cookie")
    return command


c.ServerProxy.servers = {
    "photoswitchlab": {
        "command": photoswitchlab_command,
        "unix_socket": True,
        "timeout": 60,
        "absolute_url": False,
        "environment": {
            "PATH": str(app_bin) + os.pathsep + os.environ["PATH"],
            "PYTHONNOUSERSITE": "1",
            "MPLBACKEND": "Agg",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        },
        "launcher_entry": {"title": "Molekulare Photoschalter"},
    }
}
