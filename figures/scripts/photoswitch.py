"""Source for photoswitch.svg; run directly to regenerate this figure."""

from style import TEXT, export, run
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from scipy.signal import argrelextrema


def draw():
    x = np.linspace(-1.0, 1.0, 1000)
    y0 = 2.7 * x**4 - 1.6 * x**2 + 0.2 * x
    y = y0 - np.min(y0)

    mask = y <= 1.0

    plt.plot(x[mask], y[mask])

    # find the two minima positions

    # indices of local minima
    mins = argrelextrema(y, np.less)[0]
    min_positions = [(x[i], y[i]) for i in mins]

    # Pick the two lowest ones (just in case there are small numerical bumps)
    min_positions = sorted(min_positions, key=lambda t: t[1])[:2]

    for (xm, ym), conf in zip(min_positions, ["trans", "cis"]):
        plt.text(xm, ym + 0.08, conf, ha="center", va="bottom")

    plt.plot([x[mask].min(), x[mask].max()], [1.5, 1.5], color="C1", ls="--")
    plt.text(0.89, 1.54, "angeregter Zustand", ha="right", va="bottom", color="C1")
    plt.text(0.89, 0.05, "Grundzustand", ha="right", va="bottom", color="C0")

    arrow_vert = patches.FancyArrowPatch(
        (-0.57, 0.19),
        (-0.57, 1.45),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)

    arrow_vert = patches.FancyArrowPatch(
        (0.51, 1.45),
        (0.51, 0.4),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)

    plt.xticks([])
    plt.yticks([])
    plt.xlabel("Reaktionskoordinate")
    plt.ylabel("Energie")
    plt.ylim(-0.1, 1.7)


def render(output_dir=None, formats=("svg",)):
    export(draw, "photoswitch", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
