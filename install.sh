#!/bin/sh
set -eu

REPO_URL="https://github.com/mvondomaros-lab/achprak"
REPO_DIR="${HOME}/achprak"
ENV_NAME="hub"
KERNEL_NAME="achprak"
KERNEL_DISPLAY_NAME="AChPrak"
NOTEBOOK_RELATIVE_PATH="notebooks/achprak.ipynb"

info() {
  printf '%s\n' "$*"
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

install_pixi() {
  if have_cmd pixi; then
    info "pixi already installed: $(command -v pixi)"
    return
  fi

  info "Installing pixi..."
  if have_cmd curl; then
    curl -fsSL https://pixi.sh/install.sh | sh
  elif have_cmd wget; then
    wget -qO- https://pixi.sh/install.sh | sh
  else
    fail "Neither curl nor wget is available."
  fi

  PIXI_BIN_DIR="${HOME}/.pixi/bin"
  if [ -x "${PIXI_BIN_DIR}/pixi" ]; then
    PATH="${PIXI_BIN_DIR}:${PATH}"
    export PATH
  fi

  have_cmd pixi || fail "pixi installation finished, but pixi is not on PATH."
}

clone_or_update_repo() {
  if [ -d "${REPO_DIR}/.git" ]; then
    info "Repository already exists, updating ${REPO_DIR}..."
    git -C "${REPO_DIR}" pull --ff-only || fail "git pull failed in ${REPO_DIR}"
  else
    info "Cloning repository into ${REPO_DIR}..."
    git clone "${REPO_URL}" "${REPO_DIR}" || fail "git clone failed"
  fi
}

install_env() {
  info "Installing pixi environment '${ENV_NAME}'..."
  cd "${REPO_DIR}"
  pixi install -e "${ENV_NAME}" || fail "pixi install failed"
}

register_kernel() {
  info "Registering Jupyter kernel '${KERNEL_NAME}'..."

  ENV_BIN="${REPO_DIR}/.pixi/envs/${ENV_NAME}/bin"
  ENV_PYTHON="${ENV_BIN}/python"
  KERNEL_DIR="${HOME}/.local/share/jupyter/kernels/${KERNEL_NAME}"

  [ -x "${ENV_PYTHON}" ] || fail "Expected Python not found: ${ENV_PYTHON}"

  mkdir -p "${KERNEL_DIR}"

  cat > "${KERNEL_DIR}/kernel.json" <<EOF
{
  "argv": [
    "${ENV_PYTHON}",
    "-m",
    "ipykernel_launcher",
    "-f",
    "{connection_file}"
  ],
  "display_name": "${KERNEL_DISPLAY_NAME}",
  "language": "python",
  "metadata": {
    "debugger": true
  },
  "env": {
    "PATH": "${ENV_BIN}:${PATH}"
  }
}
EOF

  info "Kernel registered at ${KERNEL_DIR}"
}

patch_notebook_metadata() {
  NOTEBOOK_PATH="${REPO_DIR}/${NOTEBOOK_RELATIVE_PATH}"
  [ -f "${NOTEBOOK_PATH}" ] || fail "Notebook not found: ${NOTEBOOK_PATH}"

  info "Patching notebook metadata to use kernel '${KERNEL_NAME}'..."

  cd "${REPO_DIR}"
  pixi run -e "${ENV_NAME}" python - <<EOF
import json
from pathlib import Path

path = Path("${NOTEBOOK_PATH}")
nb = json.loads(path.read_text(encoding="utf-8"))

nb.setdefault("metadata", {})
nb["metadata"]["kernelspec"] = {
    "display_name": "${KERNEL_DISPLAY_NAME}",
    "language": "python",
    "name": "${KERNEL_NAME}",
}

path.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Updated kernelspec in {path}")
EOF
}

print_final_instructions() {
  NOTEBOOK_PATH="${REPO_DIR}/${NOTEBOOK_RELATIVE_PATH}"
  [ -f "${NOTEBOOK_PATH}" ] || fail "Notebook not found: ${NOTEBOOK_PATH}"

  printf '\n'
  printf '============================================================\n'
  printf ' AChPrak installation complete\n'
  printf '============================================================\n'
  printf '\n'
  printf 'Next steps in JupyterLab:\n'
  printf '\n'
  printf '1. In the file browser on the left, open this folder:\n'
  printf '   %s\n' "${REPO_DIR}/notebooks"
  printf '\n'
  printf '2. Double-click this notebook file:\n'
  printf '   achprak.ipynb\n'
  printf '\n'
  printf '3. When the notebook opens, check the kernel shown in the\n'
  printf '   top-right corner.\n'
  printf '\n'
  printf '4. It should be:\n'
  printf '   %s\n' "${KERNEL_DISPLAY_NAME}"
  printf '\n'
  printf '5. If a different kernel is selected, switch manually:\n'
  printf '   Kernel  ->  Change Kernel...  ->  %s\n' "${KERNEL_DISPLAY_NAME}"
  printf '\n'
  printf 'Notebook path:\n'
  printf '   %s\n' "${NOTEBOOK_PATH}"
  printf '\n'
  printf 'If you already had the notebook open, close it and open it\n'
  printf 'again so that JupyterLab picks up the updated kernel setting.\n'
  printf '\n'
  printf 'If something does not work, first check that the notebook is\n'
  printf 'really running with the kernel "%s".\n' "${KERNEL_NAME}"
  printf '\n'
  printf '============================================================\n'
  printf '\n'
}

main() {
  have_cmd git || fail "git is required but not installed."

  install_pixi
  clone_or_update_repo
  install_env
  register_kernel
  patch_notebook_metadata
  print_final_instructions

  info "Done."
}

main "$@"