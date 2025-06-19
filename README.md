# Einführungsversuch in die Theoretische Chemie

## Setup

1. Miniconda installieren.
2. Conda-Umgebung installieren und aktivieren.
    ```bash
    conda env create --file environment.yml
    conda activate achprak
    ```
3. Python-Pakete mit uv installieren.
    ```bash
    uv sync
    ```
4. Jupyter Lab starten.
    ```bash
    uv run jupyter-lab achprak.ipynb
    ```
