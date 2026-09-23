"""Schematic relationships between a molecular model and calculated quantities."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from style import TEXT, export, run


def draw():
    fig = plt.gcf()
    fig.set_size_inches(9, 5)
    ax = plt.gca()
    ax.set(xlim=(0, 12), ylim=(0, 7))
    ax.set_axis_off()
    blue, ochre = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    def box(x, y, width, height, title, detail, color):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.08,rounding_size=0.12",
                facecolor="white",
                edgecolor=color,
                linewidth=1.5,
            )
        )
        ax.text(
            x + width / 2,
            y + height * 0.63,
            title,
            ha="center",
            va="center",
            weight="bold",
            color=TEXT,
            fontsize=12.5,
        )
        ax.text(
            x + width / 2,
            y + height * 0.3,
            detail,
            ha="center",
            va="center",
            color=TEXT,
            fontsize=10.5,
        )

    ax.text(
        6,
        6.65,
        "Molekülbeschreibung im Rechenmodell",
        ha="center",
        va="center",
        weight="bold",
        color=TEXT,
        fontsize=14,
    )
    box(1.5, 4.65, 4.1, 1.35, "Atomkerne", "Atomsorten und Positionen", blue)
    box(6.4, 4.65, 4.1, 1.35, "Elektronen", "Verteilung und Energie", ochre)

    for start_x in (3.55, 8.45):
        ax.add_patch(
            FancyArrowPatch(
                (start_x, 4.55),
                (6.0, 3.65),
                arrowstyle="-",
                linewidth=1.5,
                color=TEXT,
                connectionstyle="arc3,rad=0",
            )
        )
    for end_x in (2.0, 6.0, 10.0):
        ax.add_patch(
            FancyArrowPatch(
                (6.0, 3.65),
                (end_x, 2.35),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.5,
                color=TEXT,
                connectionstyle="arc3,rad=0",
            )
        )

    box(0.45, 0.65, 3.1, 1.6, "Molekülstruktur", "berechnete Atompositionen", blue)
    box(4.45, 0.65, 3.1, 1.6, "Elektronische Energie", "Unterschiede und Barrieren", blue)
    box(8.45, 0.65, 3.1, 1.6, "Elektronische Anregungen", "Lage und relative Stärke", ochre)


def render(output_dir=None, formats=("svg",)):
    export(draw, "theoretical_quantities", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
