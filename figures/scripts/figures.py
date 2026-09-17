"""Regenerate all teaching figures; each figure also has a standalone source."""

from importlib import import_module
from style import run

FIGURES = (
    "jablonski",
    "line_spectrum",
    "uvvis_spectrum",
    "profile",
    "photoswitch_mechanism",
    "substituent_effects",
)


def render(output_dir=None, formats=("svg",)):
    for module in FIGURES:
        import_module(module).render(output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
