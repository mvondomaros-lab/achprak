"""Source for substituent_effects.svg; run directly to regenerate this figure."""

from style import TEXT, export, run
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch


def draw():
    ax = plt.gca()
    ax.set(xlim=(-0.6, 5.6), ylim=(-0.65, 2.35))
    ax.set_axis_off()

    # Each system has its own ground-state energy zero. Only gaps are compared.
    cases = [
        (0.5, 0.8, "Kleinere\nAnregungsenergie", "Längere Wellenlänge\n(bathochrom)"),
        (2.5, 1.2, "Unsubstituiertes\nVergleichssystem", "Wellenlänge\ndes Vergleichssystems"),
        (4.5, 1.6, "Größere\nAnregungsenergie", "Kürzere Wellenlänge\n(hypsochrom)"),
    ]
    for center, gap, heading, wavelength in cases:
        ax.text(center, 2.12, heading, ha="center", va="center", weight="bold")
        ax.plot([center - 0.8, center + 0.8], [0, 0], color="C0")
        ax.plot([center - 0.8, center + 0.8], [gap, gap], color="C1")
        ax.text(center, -0.08, "Grundzustand", ha="center", va="top", color="C0")
        ax.text(center, gap + 0.06, "Angeregter Zustand", ha="center", va="bottom", color="C1")
        ax.add_patch(FancyArrowPatch(
            (center, 0), (center, gap), arrowstyle="->",
            linewidth=1.5, color=TEXT, mutation_scale=10,
        ))
        ax.text(center, -0.4, wavelength, ha="center", va="center")


def render(output_dir=None, formats=("svg",)):
    export(draw, "substituent_effects", output_dir, formats, display_width=700)


if __name__ == "__main__":
    run(render, __doc__)
