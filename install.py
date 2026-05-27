import json
import os
import shutil
import subprocess
from pathlib import Path

REPO_URL = "https://github.com/mvondomaros-lab/achprak"
REPO_DIR = Path.home() / "achprak"
ENV_NAME = "hub"
KERNEL_NAME = "achprak"
KERNEL_DISPLAY_NAME = "AChPrak"
PIXI_INSTALL_URL = "https://pixi.sh/install.sh"


def info(message):
    print(message, flush=True)


def fail(message):
    raise SystemExit(f"ERROR: {message}")


def run(*cmd, cwd=None):
    info("+ " + " ".join(map(str, cmd)))
    subprocess.run(cmd, cwd=cwd, check=True)


def install_pixi():
    if shutil.which("pixi"):
        info(f"pixi already installed: {shutil.which('pixi')}")
        return

    info("Installing pixi...")
    subprocess.run(
        f"curl -fsSL {PIXI_INSTALL_URL} | sh",
        shell=True,
        check=True,
        executable="/bin/sh",
    )

    pixi_bin = Path.home() / ".pixi" / "bin"
    os.environ["PATH"] = f"{pixi_bin}:{os.environ['PATH']}"

    if not shutil.which("pixi"):
        fail("pixi installation finished, but pixi is not on PATH.")


def clone_or_update_repo():
    if (REPO_DIR / ".git").is_dir():
        info(f"Repository already exists, updating {REPO_DIR}...")
        run("git", "fetch", "--all", "--prune", cwd=REPO_DIR)
        run("git", "reset", "--hard", "HEAD", cwd=REPO_DIR)
        run("git", "clean", "-fd", cwd=REPO_DIR)
        run("git", "pull", "--ff-only", cwd=REPO_DIR)
    elif REPO_DIR.exists():
        fail(f"The path already exists, but is not a git repository: {REPO_DIR}")
    else:
        info(f"Cloning repository into {REPO_DIR}...")
        run("git", "clone", REPO_URL, str(REPO_DIR))


def install_env():
    info(f"Installing pixi environment '{ENV_NAME}'...")
    run("pixi", "install", "-e", ENV_NAME, cwd=REPO_DIR)


def register_kernel():
    info(f"Registering Jupyter kernel '{KERNEL_NAME}'...")

    env_bin = REPO_DIR / ".pixi" / "envs" / ENV_NAME / "bin"
    env_python = env_bin / "python"
    kernel_dir = Path.home() / ".local" / "share" / "jupyter" / "kernels" / KERNEL_NAME
    kernel_file = kernel_dir / "kernel.json"

    if not env_python.exists():
        fail(f"Expected Python not found: {env_python}")

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
            "PATH": f"{env_bin}:{os.environ['PATH']}",
            "TF_CPP_MIN_LOG_LEVEL": "3",
        },
    }

    kernel_file.write_text(json.dumps(kernel, indent=2), encoding="utf-8")
    info(f"Kernel registered at {kernel_dir}")


def main():
    install_pixi()
    clone_or_update_repo()
    install_env()
    register_kernel()

    print()
    print("=" * 60)
    print(" AChPrak installation complete")
    print("=" * 60)
    print()
    print("Refresh JupyterLab if the kernel does not appear immediately.")
    print("Done.")


main()
