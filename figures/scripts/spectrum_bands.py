"""Source for spectrum_bands.svg; run directly to regenerate this figure."""

from style import STICK_WIDTH, MARKER_SIZE, export, run
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

# Gaussian standard deviation in eV, matching achprak.uvvis.SIGMA.
SIGMA_EV = 0.15


def draw():
    x = np.linspace(1.5, 5.5, 1000)
    a = sum(
        strength * np.exp(-0.5 * ((x - energy) / SIGMA_EV) ** 2)
        for energy, strength in [(3.0, 0.5), (4.0, 0.3)]
    )

    plt.plot(
        [3.0, 3.0],
        [0.0, 0.5],
        color="C1",
        linewidth=STICK_WIDTH,
        marker="o",
        markevery=[1],
        markersize=MARKER_SIZE,
        markeredgewidth=0,
    )
    plt.plot(
        [4.0, 4.0],
        [0.0, 0.3],
        color="C1",
        linewidth=STICK_WIDTH,
        marker="o",
        markevery=[1],
        markersize=MARKER_SIZE,
        markeredgewidth=0,
    )
    plt.plot(x, a, color="C0")
    plt.xlim(1.4, 5.6)
    plt.ylim(0, 0.6)
    plt.xlabel(r"Energie / eV")
    plt.ylabel(r"Relative Absorption")
    plt.gca().xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:.1f}".replace(".", ","))
    )
    plt.gca().yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:.1f}".replace(".", ","))
    )


def render(output_dir=None, formats=("svg",)):
    export(draw, "spectrum_bands", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
