# Practical exercise introducing Theoretical Chemistry to first-year students of Chemistry

> [!NOTE]
> The exercise is available in German, only.

## Fundamentals

Available on GitHub Pages.

[![Docs](https://img.shields.io/badge/docs-github%20pages-blue)](https://mvondomaros-lab.github.io/achprak/)

## Offline Setup

1. Install [pixi](https://pixi.sh).
2. Clone the repository.
    ```bash
    git clone https://github.com/mvondomaros-lab/achprak.git
   ```
3. Install python dependencies using `pixi`.
    ```bash
    cd achprak 
    pixi install -e local
    ```
4. Start the Jupyter Lab server.
    ```bash
    pixi run -e local jupyter-lab achprak.ipynb
    ```

> [!NOTE]
> Developers: Use `dev` instead of `local`  for development.