"""Distinguish experimental checks from computational reference comparisons."""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from style import TEXT, export, run


def draw():
    fig = plt.gcf()
    fig.set_size_inches(9, 5.5)
    ax = plt.gca()
    ax.set(xlim=(0, 14), ylim=(0, 8))
    ax.set_axis_off()
    blue = plt.rcParams["axes.prop_cycle"].by_key()["color"][0]

    def box(x, y, width, title, detail):
        height = 1.55
        ax.add_patch(
            FancyBboxPatch(
                (x, y), width, height,
                boxstyle="round,pad=0.08,rounding_size=0.12",
                facecolor="white", edgecolor=blue, linewidth=1.5,
            )
        )
        ax.text(
            x + width / 2, y + 1.1, title,
            ha="center", va="center", weight="bold", color=TEXT, fontsize=12,
        )
        ax.text(
            x + width / 2, y + 0.48, detail,
            ha="center", va="center", color=TEXT, fontsize=10.5,
            linespacing=1.35,
        )

    # Axis margins include the rounded-box padding and stroke width.
    box(
        2.6, 5.85, 8.8, "Vorhersage des Rechenmodells",
        "Zum Beispiel: Verschiebung einer Absorptionsbande\ndurch einen Substituenten",
    )
    ax.plot([7, 7], [5.7, 5.1], color=blue, linewidth=1.5)
    ax.plot([3.65, 10.35], [5.1, 5.1], color=blue, linewidth=1.5)
    for center in (3.65, 10.35):
        ax.add_patch(FancyArrowPatch(
            (center, 5.1), (center, 4.55), arrowstyle="-|>",
            mutation_scale=12, linewidth=1.5, color=blue,
        ))

    box(
        0.7, 2.85, 5.9, "Vergleich mit Messwerten",
        "Dieselben Moleküle und dieselbe Größe\nunter vergleichbaren Bedingungen",
    )
    box(
        7.4, 2.85, 5.9, "Vergleich mit Referenzrechnungen",
        "Verfahren mit belegter Genauigkeit\nfür die untersuchte Größe",
    )

    for center, title, detail in (
        (3.65, "Prüfung am Experiment",
         "Berechnete und gemessene\nBandenverschiebungen vergleichen"),
        (10.35, "Beurteilung der Näherungen",
         "Abweichungen von der\nReferenzrechnung untersuchen"),
    ):
        ax.add_patch(FancyArrowPatch(
            (center, 2.68), (center, 2.2), arrowstyle="-|>",
            mutation_scale=12, linewidth=1.5, color=blue,
        ))
        ax.text(center, 1.9, title, ha="center", va="center",
                weight="bold", color=TEXT, fontsize=10.5)
        ax.text(center, 1.25, detail, ha="center", va="center",
                color=TEXT, fontsize=10.5, linespacing=1.35)

    ax.text(
        7, 0.35, "Vergleiche für mehrere Moleküle helfen, die Zuverlässigkeit eines Trends einzuschätzen.",
        ha="center", va="center", color=TEXT, fontsize=10,
    )


def render(output_dir=None, formats=("svg",)):
    export(draw, "prediction_cycle", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
