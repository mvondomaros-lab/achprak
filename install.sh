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

  PIXI_BIN="${HOME}/.pixi/bin"
  if [ -x "${PIXI_BIN}/pixi" ]; then
    PATH="${PIXI_BIN}:${PATH}"
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
  cd "${REPO_DIR}"
  pixi run -e "${ENV_NAME}" python -m ipykernel install \
    --user \
    --name "${KERNEL_NAME}" \
    --display-name "${KERNEL_DISPLAY_NAME}" \
    || fail "kernel registration failed"
}

open_notebook() {
  NOTEBOOK_PATH="${REPO_DIR}/${NOTEBOOK_RELATIVE_PATH}"

  [ -f "${NOTEBOOK_PATH}" ] || fail "Notebook not found: ${NOTEBOOK_PATH}"

  if have_cmd jupyter; then
    info "Opening notebook in JupyterLab..."
    jupyter lab "${NOTEBOOK_PATH}" >/dev/null 2>&1 &
    info "Notebook launch requested: ${NOTEBOOK_PATH}"
  else
    info "JupyterLab command not found on PATH."
    info "Setup is complete."
    info "Open this notebook manually in your running JupyterLab session:"
    info "  ${NOTEBOOK_PATH}"
  fi
}

main() {
  have_cmd git || fail "git is required but not installed."

  install_pixi
  clone_or_update_repo
  install_env
  register_kernel
  open_notebook

  info "Done."
}

main "$@"
