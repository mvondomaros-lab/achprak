"""Shared export and appearance, aligned with plotStyle in web/static/app.js."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cycler import cycler
from matplotlib.ticker import FuncFormatter, MaxNLocator

TEXT = "#192d43"
STYLE = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.edgecolor": "#dce4ed",
    "axes.linewidth": 0.75,
    "axes.labelcolor": "#586b80",
    "axes.labelpad": 9,
    "text.color": TEXT,
    "xtick.color": "#586b80",
    "ytick.color": "#586b80",
    "grid.color": "#e7edf5",
    "grid.linewidth": 0.75,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.major.pad": 7,
    "ytick.major.pad": 7,
    "lines.linewidth": 1.5,
    "axes.prop_cycle": cycler(color=["#165de1", "#c77825"]),
    # Outline glyphs so the website does not depend on installed viewer fonts.
    "svg.fonttype": "path",
    "svg.hashsalt": "achprak-teaching",
}


def export(draw, name, output_dir=None, formats=("svg",)):
    output_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
        ax.set_axisbelow(True)
        ax.yaxis.grid(True)
        ax.spines[["top", "right"]].set_visible(False)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=7, steps=[1, 2, 5, 10]))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_formatter(
                FuncFormatter(lambda value, _: f"{value:g}".replace(".", ","))
            )
        try:
            draw()
            for extension in formats:
                metadata = {"Date": None} if extension == "svg" else None
                fig.savefig(
                    output_dir / f"{name}.{extension}", dpi=300, metadata=metadata
                )
        finally:
            plt.close(fig)


def run(render, description):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--format", choices=("svg", "png", "both"), default="svg")
    args = parser.parse_args()
    formats = ("svg", "png") if args.format == "both" else (args.format,)
    render(args.output_dir, formats)
