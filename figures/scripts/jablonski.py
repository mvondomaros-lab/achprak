"""Source for jablonski.svg; run directly to regenerate this figure."""

from style import export, run
import matplotlib.pyplot as plt


def draw():
    plt.plot([0.1, 0.9], [0.0, 0.0], color="C0")
    plt.plot([0.1, 0.9], [3.0, 3.0], color="C0")
    plt.plot([0.1, 0.9], [4.0, 4.0], color="C0")
    plt.text(0.9, 0.02, "Grundzustand", ha="right", va="bottom")
    plt.text(0.9, 3.02, "erster angeregter Zustand", ha="right", va="bottom")
    plt.text(0.9, 4.02, "zweiter angeregter Zustand", ha="right", va="bottom")
    plt.annotate(
        "",
        xy=(0.12, 3.0),
        xytext=(0.12, 0.0),
        arrowprops=dict(arrowstyle="->", linewidth=1.5, color="C1"),
        annotation_clip=False,
    )
    plt.annotate(
        "",
        xy=(0.15, 4.0),
        xytext=(0.15, 0.0),
        arrowprops=dict(arrowstyle="->", linewidth=1.5, color="C1"),
        annotation_clip=False,
    )
    plt.text(0.17, 1.5, "Absorption von Licht", ha="left", va="center", color="C1")
    plt.ylim(-0.2, 4.4)
    plt.xticks([])
    plt.ylabel(r"Energie / eV")


def render(output_dir=None, formats=("svg",)):
    export(draw, "jablonski", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
