#!/bin/sh
set -eu

REPO_URL="https://github.com/mvondomaros-lab/achprak"
REPO_DIR="${HOME}/achprak"
ENV_NAME="hub"
KERNEL_NAME="achprak"
KERNEL_DISPLAY_NAME="AChPrak"
NOTEBOOK_RELATIVE_PATH="notebooks/achprak.ipynb"
PIXI_INSTALL_URL="https://pixi.sh/install.sh"

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
    curl -fsSL "${PIXI_INSTALL_URL}" | sh
  elif have_cmd wget; then
    wget -qO- "${PIXI_INSTALL_URL}" | sh
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
  pixi install -C "${REPO_DIR}" -e "${ENV_NAME}" || fail "pixi install failed"
}

register_kernel() {
  info "Registering Jupyter kernel '${KERNEL_NAME}'..."

  ENV_BIN="${REPO_DIR}/.pixi/envs/${ENV_NAME}/bin"
  ENV_PYTHON="${ENV_BIN}/python"
  KERNEL_DIR="${HOME}/.local/share/jupyter/kernels/${KERNEL_NAME}"
  KERNEL_FILE="${KERNEL_DIR}/kernel.json"
  TMP_KERNEL_FILE="${KERNEL_DIR}/kernel.json.tmp"

  [ -x "${ENV_PYTHON}" ] || fail "Expected Python not found: ${ENV_PYTHON}"

  mkdir -p "${KERNEL_DIR}"

  cat > "${TMP_KERNEL_FILE}" <<EOF
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

  mv "${TMP_KERNEL_FILE}" "${KERNEL_FILE}"

  info "Kernel registered at ${KERNEL_DIR}"

  # Give JupyterLab/JupyterHub a moment to notice the new kernelspec,
  # especially on slower network filesystems.
  sleep 2
}

patch_notebook_metadata() {
  NOTEBOOK_PATH="${REPO_DIR}/${NOTEBOOK_RELATIVE_PATH}"
  [ -f "${NOTEBOOK_PATH}" ] || fail "Notebook not found: ${NOTEBOOK_PATH}"

  info "Patching notebook metadata to use kernel '${KERNEL_NAME}'..."

  pixi run -C "${REPO_DIR}" -e "${ENV_NAME}" python - <<EOF
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

  case "${REPO_DIR}" in
    "${HOME}")
      REL_NOTEBOOK_DIR="notebooks"
      ;;
    "${HOME}"/*)
      REL_NOTEBOOK_DIR="${REPO_DIR#${HOME}/}/notebooks"
      ;;
    *)
      REL_NOTEBOOK_DIR="${REPO_DIR}/notebooks"
      ;;
  esac

  printf '\n'
  printf '============================================================\n'
  printf ' AChPrak installation complete\n'
  printf '============================================================\n'
  printf '\n'
  printf 'IMPORTANT: Please refresh your JupyterLab page now.\n'
  printf '\n'
  printf 'In your browser press:\n'
  printf '  F5   or   Ctrl+R\n'
  printf '\n'
  printf 'This step is necessary so that JupyterLab detects the new\n'
  printf 'AChPrak kernel.\n'
  printf '\n'
  printf 'After refreshing JupyterLab:\n'
  printf '\n'
  printf '1. In the file browser on the left, open this folder:\n'
  printf '   %s\n' "${REL_NOTEBOOK_DIR}"
  printf '\n'
  printf '2. Double-click this notebook file:\n'
  printf '   achprak.ipynb\n'
  printf '\n'
  printf '3. Check the kernel shown in the top-right corner.\n'
  printf '\n'
  printf '4. It should be:\n'
  printf '   %s\n' "${KERNEL_DISPLAY_NAME}"
  printf '\n'
  printf '5. If a different kernel is selected:\n'
  printf '   Kernel  ->  Change Kernel...  ->  %s\n' "${KERNEL_DISPLAY_NAME}"
  printf '\n'
  printf 'If the notebook was already open, close it and open it again.\n'
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