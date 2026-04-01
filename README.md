# Practical Exercise: Introducing Theoretical Chemistry to First-Year Chemistry Students

> [!NOTE]
> This exercise is currently available in German only.

## Overview

The materials are available on GitHub Pages:

[![Docs](https://img.shields.io/badge/docs-github%20pages-blue)](https://mvondomaros-lab.github.io/achprak/)

## Local Setup

1. Install [pixi](https://pixi.sh).
2. Clone the repository:

    ```bash
    git clone https://github.com/mvondomaros-lab/achprak.git
    ```

3. Enter the project directory and install the dependencies:

    ```bash
    cd achprak
    pixi install -e local
    ```

4. Start JupyterLab with the exercise notebook:

    ```bash
    pixi run -e local jupyter-lab notebooks/achprak.ipynb
    ```

> [!NOTE]
> For development, use the `dev` environment instead of `local`.

## Installer

For easy deployment on JupyterHub instances, an installer script is available:

```bash
curl -fsSL https://raw.githubusercontent.com/mvondomaros-lab/achprak/main/install.sh | sh
```
