import json
import os
import subprocess
import tarfile
import urllib.request
from pathlib import Path

REPO_URL = "https://github.com/mvondomaros-lab/achprak"
REPO_DIR = Path.home() / "achprak"
ENV_NAME = "hub"
KERNEL_NAME = "achprak"
KERNEL_DISPLAY_NAME = "AChPrak"
PIXI_URL = "https://github.com/prefix-dev/pixi/releases/latest/download/pixi-x86_64-unknown-linux-musl.tar.gz"

HOME = Path.home()
PIXI_BIN = HOME / ".pixi" / "bin"
PIXI = PIXI_BIN / "pixi"

os.environ["PIXI_CACHE_DIR"] = f"/tmp/pixi-cache-{os.environ['USER']}"


def run(*cmd, cwd=None):
    print("+", *cmd, flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def install_pixi():
    if not PIXI.exists():
        print("Installing pixi...", flush=True)
        PIXI_BIN.mkdir(parents=True, exist_ok=True)

        archive = PIXI_BIN / "pixi.tar.gz"
        urllib.request.urlretrieve(PIXI_URL, archive)

        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(PIXI_BIN)

        archive.unlink()
        PIXI.chmod(0o755)

    os.environ["PATH"] = f"{PIXI_BIN}:{os.environ['PATH']}"


def clone_or_update_repo():
    if (REPO_DIR / ".git").is_dir():
        print(f"Updating {REPO_DIR}...", flush=True)
        run("git", "fetch", "--all", "--prune", cwd=REPO_DIR)
        run("git", "reset", "--hard", "HEAD", cwd=REPO_DIR)
        run("git", "clean", "-fd", cwd=REPO_DIR)
        run("git", "pull", "--ff-only", cwd=REPO_DIR)
    elif REPO_DIR.exists():
        raise SystemExit(f"ERROR: {REPO_DIR} exists but is not a git repository.")
    else:
        print(f"Cloning into {REPO_DIR}...", flush=True)
        run("git", "clone", REPO_URL, str(REPO_DIR))


def install_env():
    run(str(PIXI), "install", "-e", ENV_NAME, cwd=REPO_DIR)


def register_kernel():
    env_bin = REPO_DIR / ".pixi" / "envs" / ENV_NAME / "bin"
    env_python = env_bin / "python"
    kernel_dir = HOME / ".local" / "share" / "jupyter" / "kernels" / KERNEL_NAME

    kernel_dir.mkdir(parents=True, exist_ok=True)

    kernel = {
        "argv": [
            str(env_python),
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ],
        "display_name": KERNEL_DISPLAY_NAME,
        "language": "python",
        "metadata": {"debugger": True},
        "env": {
            "PATH": f"{env_bin}:{PIXI_BIN}:{os.environ['PATH']}",
            "TF_CPP_MIN_LOG_LEVEL": "3",
        },
    }

    (kernel_dir / "kernel.json").write_text(
        json.dumps(kernel, indent=2),
        encoding="utf-8",
    )

    print(f"Kernel registered: {kernel_dir}", flush=True)


install_pixi()
clone_or_update_repo()
install_env()
register_kernel()

print("\nAChPrak installation complete. Refresh JupyterLab if needed.")
