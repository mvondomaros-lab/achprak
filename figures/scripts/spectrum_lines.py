"""Source for spectrum_lines.svg; run directly to regenerate this figure."""

from style import export, run
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def draw():
    plt.plot([3.0, 3.0], [0.0, 0.5], color="C1")
    plt.plot([4.0, 4.0], [0.0, 0.3], color="C1")
    plt.xlim(1.4, 5.6)
    plt.ylim(0, 0.6)
    plt.xlabel(r"Energie / eV")
    plt.ylabel(r"Relative Absorption / a.u.")
    plt.gca().xaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:.1f}".replace(".", ","))
    )
    plt.gca().yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:.1f}".replace(".", ","))
    )


def render(output_dir=None, formats=("svg",)):
    export(draw, "spectrum_lines", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
