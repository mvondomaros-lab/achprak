"""Draw the C–N=N–C illustration for the web app's dihedral-angle popover."""

from pathlib import Path

from style import TEXT, export, run
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle

# The popover's 538 px content width renders 15 pt labels at 14 CSS px,
# matching its explanatory text. Atom/angle symbols are slightly larger.
LABEL_SIZE = 15
SYMBOL_SIZE = 17


def draw():
    # Schematic views, not calculated coordinates or a measured angle.
    fig = plt.gcf()
    fig.set_size_inches(8, 3.2)
    ax = plt.gca()
    ax.set(xlim=(-0.2, 9.2), ylim=(-1.5, 1.85), aspect="equal")
    ax.set_axis_off()
    blue, ochre = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    def bond(start, end, double=False):
        for offset in (-0.045, 0.045) if double else (0,):
            ax.plot(
                [start[0], end[0]],
                [start[1] + offset, end[1] + offset],
                color=blue,
                linewidth=1.5,
                zorder=2,
            )

    def atom(position, element, radius=0.23):
        ax.add_patch(
            Circle(
                position,
                radius,
                facecolor="white",
                edgecolor=blue,
                linewidth=1.5,
                zorder=3,
            )
        )
        ax.text(
            *position,
            element,
            ha="center",
            va="center",
            fontsize=SYMBOL_SIZE,
            color=TEXT,
            zorder=4,
        )

    # Four-atom chain with the viewing direction along the central N=N bond.
    carbon1, nitrogen1 = (1.9, -0.8), (2.7, 0)
    nitrogen2, carbon2 = (3.8, 0), (4.6, 0.8)
    bond(carbon1, nitrogen1)
    bond(nitrogen1, nitrogen2, double=True)
    bond(nitrogen2, carbon2)
    for position, element in zip(
        (carbon1, nitrogen1, nitrogen2, carbon2), ("C", "N", "N", "C")
    ):
        atom(position, element)
    ax.annotate(
        "",
        xy=(2.25, 0),
        xytext=(0, 0),
        arrowprops={"arrowstyle": "->", "color": ochre, "lw": 1.5},
    )
    ax.text(0, 0.25, "Blickrichtung", fontsize=LABEL_SIZE, color=ochre)

    # End-on projection: the N atoms coincide, and the N–C projections define φ.
    center, lower, upper = (6.7, 0), (7.7, -1), (7.7, 1)
    bond(center, lower)
    bond(center, upper)
    ax.add_patch(
        Circle(
            center, 0.32, facecolor="white", edgecolor=blue, linewidth=1.5, zorder=2.5
        )
    )
    atom(center, "N")
    atom(lower, "C")
    atom(upper, "C")
    ax.add_patch(
        Arc(center, 1.3, 1.3, theta1=-45, theta2=45, color=ochre, linewidth=1.5)
    )
    ax.text(7.55, 0, "φ", color=ochre, fontsize=SYMBOL_SIZE, ha="center", va="center")
    ax.text(6.9, 1.55, "Blick entlang N=N", ha="center", fontsize=LABEL_SIZE, color=TEXT)
    ax.text(
        6.9,
        -1.45,
        "N-Atome hintereinander",
        ha="center",
        fontsize=LABEL_SIZE,
        color=plt.rcParams["axes.labelcolor"],
    )


def render(output_dir=None, formats=("svg",)):
    # Keep the canonical asset inside package data so installed/offline apps work.
    if output_dir is None:
        output_dir = Path(__file__).resolve().parents[2] / "src/achprak/web/static"
    export(draw, "dihedral", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
