# Use a Binder-friendly Jupyter base image (already has JupyterLab, non-root user, etc.)
FROM jupyter/minimal-notebook:python-3.11

# Become root briefly to install system deps you might need (add more here if required)
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git && \
    rm -rf /var/lib/apt/lists/*

# Back to the default non-root user that Binder expects
USER ${NB_USER}
WORKDIR /home/jovyan/work

# Install pixi for per-project environment management
RUN curl -fsSL https://pixi.sh/install.sh | bash && \
    echo 'export PATH="$HOME/.pixi/bin:$PATH"' >> ~/.bashrc
ENV PATH="/home/jovyan/.pixi/bin:${PATH}"

# Copy your repo into the image with correct ownership
COPY --chown=${NB_UID}:${NB_GID} . .

# Install project dependencies from pyproject.toml / pixi.lock
RUN pixi install

# (Optional) ensure the working directory is where your notebook lives
ENV REPO_DIR="/home/jovyan/work"
WORKDIR ${REPO_DIR}

# Default command (Binder also manages this, but good for local runs)
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--no-browser", "--ServerApp.token="]

