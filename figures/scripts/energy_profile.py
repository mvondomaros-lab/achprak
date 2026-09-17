"""Source for energy_profile.svg; run directly to regenerate this figure."""

from style import TEXT, REFERENCE, export, run
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

    # add a small curved double-headed arrow at each

    xrange = x.max() - x.min()
    span = 0.1 * xrange  # 10% of total width

    for (xm, ym), conf in zip(min_positions, ["trans", "cis"]):
        arrow = patches.FancyArrowPatch(
            (xm - span / 2, ym + 0.07),
            (xm + span / 2, ym + 0.07),
            arrowstyle="<->",
            connectionstyle="arc3,rad=0.4",
            linewidth=1.5,
            edgecolor=TEXT,
            mutation_scale=10,
        )
        plt.gca().add_patch(arrow)
        plt.text(xm, ym + 0.08, conf, ha="center", va="bottom")

    # indices of local maxima
    max_indices = argrelextrema(y, np.greater)[0]
    # pick the one with the highest value
    imax = max_indices[np.argmax(y[max_indices])]
    x_ts, y_ts = x[imax], y[imax]

    arrow_ts = patches.FancyArrowPatch(
        (x_ts - span / 2, y_ts + 0.01),
        (x_ts + span / 2, y_ts + 0.01),
        arrowstyle="<->",
        connectionstyle="arc3,rad=-0.4",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_ts)
    plt.text(x_ts, y_ts + 0.06, "TS", ha="center", va="bottom")

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
