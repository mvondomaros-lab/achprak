#!/usr/bin/env bash
set -euo pipefail

# 1) Install pixi
curl -fsSL https://pixi.sh/install.sh | bash
echo 'export PATH="$HOME/.pixi/bin:$PATH"' >> "$HOME/.bashrc"
export PATH="$HOME/.pixi/bin:$PATH"

# 2) Create/restore the project env from lockfile
pixi install --locked || pixi install

# 3) Make sure Jupyter + ipykernel live in the pixi env
#    (if not already declared in your pyproject/pixi.lock)
if ! pixi run python -c "import jupyterlab, ipykernel" 2>/dev/null; then
  pixi add jupyterlab ipykernel
fi

# 4) Register a kernel so VS Code / Jupyter can find it by name
ENV_NAME="achprak"
pixi run python -m ipykernel install --user --name "$ENV_NAME" --display-name "Python (pixi: $ENV_NAME)"

# 5) Optional: convenience script to start Jupyter Lab
cat > $HOME/start-jupyter.sh <<'EOF'
#!/usr/bin/env bash
export PATH="$HOME/.pixi/bin:$PATH"
pixi run jupyter lab --ip=0.0.0.0 --no-browser --ServerApp.token=
EOF
chmod +x $HOME/start-jupyter.sh

