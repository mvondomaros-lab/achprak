"""Shared export and appearance, aligned with plotStyle in web/static/app.js."""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from achprak.plot_style import (
    STYLE,
    TEXT,
    REFERENCE,
    STICK_WIDTH,
    MARKER_SIZE,
    style_axes,
)


def export(draw, name, output_dir=None, formats=("svg",)):
    output_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(STYLE):
        fig, ax = plt.subplots(figsize=(8, 4.8), layout="constrained")
        style_axes(ax)
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
