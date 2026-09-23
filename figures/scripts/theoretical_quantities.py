"""Connect the shared physical description to three distinct calculation tasks."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from style import (
    TEXT, DIAGRAM_WIDTH, DIAGRAM_BODY, DIAGRAM_HEADING, DIAGRAM_TITLE, export, run,
)


def draw():
    fig = plt.gcf()
    fig.set_size_inches(DIAGRAM_WIDTH, 6)
    ax = plt.gca()
    ax.set(xlim=(0, 15), ylim=(0, 7))
    ax.set_axis_off()
    blue = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]

    def box(x, y, width, height, title, detail):
        ax.add_patch(
            FancyBboxPatch(
                (x, y),
                width,
                height,
                boxstyle="round,pad=0.08,rounding_size=0.12",
                facecolor="white",
                edgecolor=blue,
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
            fontsize=DIAGRAM_HEADING,
        )
        ax.text(
            x + width / 2,
            y + height * 0.3,
            detail,
            ha="center",
            va="center",
            color=TEXT,
            fontsize=DIAGRAM_BODY,
            linespacing=1.35,
        )

    ax.text(
        7.5,
        6.65,
        "Struktur, Energie und Spektrum im Rechenmodell",
        ha="center",
        va="center",
        weight="bold",
        color=TEXT,
        fontsize=DIAGRAM_TITLE,
    )
    box(
        2.5, 4.65, 10, 1.25,
        "Atomkerne und Elektronen",
        "Ihre Wechselwirkungen werden näherungsweise beschrieben.",
    )

    # One common foundation; the branches denote tasks, not particle categories.
    ax.plot([7.5, 7.5], [4.55, 4.05], color=blue, linewidth=1.5)
    ax.plot([2.5, 12.5], [4.05, 4.05], color=blue, linewidth=1.5)
    for x in (2.5, 7.5, 12.5):
        ax.add_patch(
            FancyArrowPatch(
                (x, 4.05),
                (x, 3.6),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.5,
                color=blue,
                connectionstyle="arc3,rad=0",
            )
        )

    tasks = (
        (2.5, "Strukturen optimieren", "Atompositionen verändern,\num die Energie zu verringern", "Molekülstrukturen", "Bindungslängen und Winkel"),
        (7.5, "Energien vergleichen", "Energien für verschiedene\nStrukturen berechnen", "Energieunterschiede", "z. B. zwischen cis und trans"),
        (12.5, "Anregungen berechnen", "Energien und Stärken\nelektronischer Anregungen\nbestimmen", "Absorptionsspektren", "Lage und relative Stärke\nder Banden"),
    )
    for x, task, description, result, detail in tasks:
        ax.text(x, 3.28, task, ha="center", va="center", weight="bold", color=TEXT, fontsize=DIAGRAM_HEADING)
        ax.text(x, 2.62, description, ha="center", va="center", color=TEXT, fontsize=DIAGRAM_BODY, linespacing=1.35)
        ax.add_patch(FancyArrowPatch((x, 2.12), (x, 1.7), arrowstyle="-|>", mutation_scale=12, linewidth=1.5, color=blue))
        box(x - 2.25, 0.3, 4.5, 1.25, result, detail)


def render(output_dir=None, formats=("svg",)):
    export(draw, "theoretical_quantities", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
