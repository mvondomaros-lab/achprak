"""Source for energy_levels.svg; run directly to regenerate this figure."""

from style import TEXT, export, run
import matplotlib.pyplot as plt


def draw():
    plt.plot([0.1, 0.9], [0.0, 0.0], color="C0")
    plt.plot([0.1, 0.9], [3.0, 3.0], color="C1")
    plt.plot([0.1, 0.9], [4.0, 4.0], color="C1")
    plt.text(0.9, 0.02, "Grundzustand", ha="right", va="bottom")
    plt.text(0.1, 3.08, "Erster angeregter Zustand", ha="left", va="bottom", color="C1")
    plt.text(0.1, 4.08, "Zweiter angeregter Zustand", ha="left", va="bottom", color="C1")
    plt.annotate(
        "",
        xy=(0.18, 3.0),
        xytext=(0.18, 0.0),
        arrowprops=dict(arrowstyle="->", linewidth=1.5, color=TEXT),
        annotation_clip=False,
    )
    plt.annotate(
        "",
        xy=(0.65, 4.0),
        xytext=(0.65, 0.0),
        arrowprops=dict(arrowstyle="->", linewidth=1.5, color=TEXT),
        annotation_clip=False,
    )
    plt.text(0.22, 1.5, "Photon\n3,0 eV", ha="left", va="center", color=TEXT, linespacing=1.5)
    plt.text(0.69, 1.5, "Photon\n4,0 eV", ha="left", va="center", color=TEXT, linespacing=1.5)
    plt.xlim(0.06, 0.94)
    plt.ylim(-0.2, 4.4)
    plt.xticks([])
    plt.yticks([0, 3, 4])
    plt.ylabel("Relative Energie / eV")
    plt.grid(False)
    plt.gca().spines["bottom"].set_visible(False)


def render(output_dir=None, formats=("svg",)):
    export(draw, "energy_levels", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
