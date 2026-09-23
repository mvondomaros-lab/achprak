"""Source for energy_profile.svg; run directly to regenerate this figure."""

from style import TEXT, REFERENCE, export, run
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
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

    xrange = x.max() - x.min()
    span = 0.1 * xrange  # 10% of total width

    def potential_arrow(center):
        # Follow the same potential, translated vertically by a constant gap.
        arrow_x = np.linspace(center - span / 2, center + span / 2, 101)
        arrow_y = (
            2.7 * arrow_x**4 - 1.6 * arrow_x**2 + 0.2 * arrow_x
            - np.min(y0) + 0.045
        )
        arrow = patches.FancyArrowPatch(
            path=Path(np.column_stack((arrow_x, arrow_y))),
            arrowstyle="<->",
            linewidth=1.5,
            edgecolor=TEXT,
            mutation_scale=10,
        )
        plt.gca().add_patch(arrow)

    for (xm, ym), conf in zip(min_positions, ["trans", "cis"]):
        potential_arrow(xm)
        plt.text(xm, ym + 0.12, conf, ha="center", va="bottom")

    # indices of local maxima
    max_indices = argrelextrema(y, np.greater)[0]
    # pick the one with the highest value
    imax = max_indices[np.argmax(y[max_indices])]
    x_ts, y_ts = x[imax], y[imax]

    potential_arrow(x_ts)
    plt.text(x_ts, y_ts + 0.10, "TS", ha="center", va="bottom")

    plt.plot([-0.7, 0.0], [0.0, 0.0], **REFERENCE)
    plt.plot([-0.6, 0.1], [y_ts, y_ts], **REFERENCE)
    arrow_vert = patches.FancyArrowPatch(
        (-0.25, 0.0),
        (-0.25, y_ts),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)
    plt.text(-0.2, 0.3 * y_ts, r"$\Delta E^\ddagger$", ha="left", va="bottom")

    plt.xticks([])
    plt.yticks([])
    plt.xlabel("Reaktionskoordinate")
    plt.ylabel("Energie")


def render(output_dir=None, formats=("svg",)):
    export(draw, "energy_profile", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
