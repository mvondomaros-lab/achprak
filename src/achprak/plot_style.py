"""Plot conventions shared by teaching figures and scientific exports.

Keep the CSS-pixel equivalents in web/static/app.js plotStyle aligned.
"""

from cycler import cycler
from matplotlib.ticker import FuncFormatter, MaxNLocator

PRIMARY = "#165de1"
ACCENT = "#c77825"
SELECTED = "#995511"
TEXT = "#192d43"
MUTED = "#586b80"
CURVE_WIDTH = 1.5  # Matplotlib points; equivalent to 2 CSS pixels.
STICK_WIDTH = 1.125  # Equivalent to 1.5 CSS pixels.
REFERENCE = {"color": MUTED, "linewidth": 0.75, "linestyle": (0, (4, 3))}
MARKER_SIZE = 4.5  # Diameter in points; equivalent to Chart.js radius 3 px.
STYLE = {
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 12,
    "axes.labelsize": 12.75,
    "axes.facecolor": "white",
    "figure.facecolor": "white",
    "axes.edgecolor": "#dce4ed",
    "axes.linewidth": 0.75,
    "axes.labelcolor": MUTED,
    "axes.labelpad": 9,
    "text.color": TEXT,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "grid.color": "#e7edf5",
    "grid.linewidth": 0.75,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.major.pad": 7,
    "ytick.major.pad": 7,
    "lines.linewidth": CURVE_WIDTH,
    "axes.prop_cycle": cycler(color=[PRIMARY, ACCENT]),
    # Outline glyphs so the website does not depend on installed viewer fonts.
    "svg.fonttype": "path",
    "svg.hashsalt": "achprak-teaching",
}


def style_axes(ax, *, german=True):
    """Apply common axes without changing scientific limits or labels."""
    ax.set_axisbelow(True)
    ax.yaxis.grid(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=7, steps=[1, 2, 5, 10]))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 5, 10]))
    if german:
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_formatter(
                FuncFormatter(lambda value, _: f"{value:g}".replace(".", ","))
            )
