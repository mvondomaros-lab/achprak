"""Source for substituent_effects.svg; run directly to regenerate this figure."""

from style import TEXT, REFERENCE, export, run
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def draw():
    w = 1.0
    d = 0.5

    plt.axhline(0.0, **REFERENCE)
    plt.axhline(1.0, **REFERENCE)

    plt.plot([0, w], [0, 0], color="C0")
    plt.plot([0, w], [1, 1], color="C1")
    arrow_vert = patches.FancyArrowPatch(
        (0.5 * w, 0),
        (0.5 * w, 1),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)
    plt.text(0.5 * w, 1.32, "A", weight="bold", ha="center")

    plt.plot([w + d, 2 * w + d], [0, 0], color="C0")
    plt.plot([w + d, 2 * w + d], [0.8, 0.8], color="C1")
    arrow_vert = patches.FancyArrowPatch(
        (1.5 * w + d, 0),
        (1.5 * w + d, 0.8),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)
    plt.text(1.5 * w + d, 1.32, "B.1", weight="bold", ha="center")

    plt.plot([2 * w + 2 * d, 3 * w + 2 * d], [0.2, 0.2], color="C0")
    plt.plot([2 * w + 2 * d, 3 * w + 2 * d], [1.0, 1.0], color="C1")
    arrow_vert = patches.FancyArrowPatch(
        (2.5 * w + 2 * d, 0.2),
        (2.5 * w + 2 * d, 1.0),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)
    plt.text(2.5 * w + 2 * d, 1.32, "B.2", weight="bold", ha="center")

    plt.plot([3 * w + 3 * d, 4 * w + 3 * d], [0.0, 0.0], color="C0")
    plt.plot([3 * w + 3 * d, 4 * w + 3 * d], [1.2, 1.2], color="C1")
    arrow_vert = patches.FancyArrowPatch(
        (3.5 * w + 3 * d, 0.0),
        (3.5 * w + 3 * d, 1.2),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)
    plt.text(3.5 * w + 3 * d, 1.32, "C.1", weight="bold", ha="center")

    plt.plot([4 * w + 4 * d, 5 * w + 4 * d], [-0.2, -0.2], color="C0")
    plt.plot([4 * w + 4 * d, 5 * w + 4 * d], [1.0, 1.0], color="C1")
    arrow_vert = patches.FancyArrowPatch(
        (4.5 * w + 4 * d, -0.2),
        (4.5 * w + 4 * d, 1.0),
        arrowstyle="->",
        connectionstyle="arc3,rad=0",
        linewidth=1.5,
        edgecolor=TEXT,
        mutation_scale=10,
    )
    plt.gca().add_patch(arrow_vert)
    plt.text(4.5 * w + 4 * d, 1.32, "C.2", weight="bold", ha="center")

    plt.grid(False)
    plt.xticks([])
    plt.yticks([])


def render(output_dir=None, formats=("svg",)):
    export(draw, "substituent_effects", output_dir, formats, display_width=700)


if __name__ == "__main__":
    run(render, __doc__)
