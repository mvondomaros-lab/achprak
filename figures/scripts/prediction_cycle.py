"""Schematic cycle from a chemical question to a tested model prediction."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from style import MUTED, TEXT, export, run


def draw():
    fig = plt.gcf()
    fig.set_size_inches(9, 4.3)
    ax = plt.gca()
    ax.set(xlim=(0, 14), ylim=(0, 6))
    ax.set_axis_off()
    blue, ochre = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    def box(x, title, detail, color):
        width, height, y = 3.1, 1.65, 2.6
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
            y + 1.08,
            title,
            ha="center",
            va="center",
            weight="bold",
            color=TEXT,
            fontsize=11.5,
        )
        ax.text(
            x + width / 2,
            y + 0.48,
            detail,
            ha="center",
            va="center",
            color=TEXT,
            fontsize=10.5,
            linespacing=1.25,
        )

    items = (
        (0.05, "Chemische Fragestellung", "untersuchte Größe", blue),
        (3.55, "Rechenmodell", "Annahmen und\nGültigkeitsbereich", blue),
        (7.05, "Vorhersage", "berechneter Wert\noder Trend", ochre),
        (10.55, "Prüfung", "Experiment oder\nReferenzrechnung", ochre),
    )
    for item in items:
        box(*item)

    for x in (3.15, 6.65, 10.15):
        ax.add_patch(
            FancyArrowPatch(
                (x, 3.43),
                (x + 0.4, 3.43),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.5,
                color=TEXT,
            )
        )

    ax.add_patch(
        FancyArrowPatch(
            (12.35, 2.5),
            (1.55, 2.5),
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.2,
            color=MUTED,
            connectionstyle="arc3,rad=-0.3",
        )
    )
    ax.text(
        7,
        0.45,
        "Bewertung und Weiterentwicklung des Modells",
        ha="center",
        va="center",
        color=MUTED,
        fontsize=11,
    )


def render(output_dir=None, formats=("svg",)):
    export(draw, "prediction_cycle", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
