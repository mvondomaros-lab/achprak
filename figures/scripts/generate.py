"""Regenerate all teaching figures; each figure also has a standalone source."""

from importlib import import_module
from style import run

FIGURES = (
    "azobenzene",
    "azobenzene_4_methoxy",
    "azobenzene_aromatic",
    "azobenzene_cis",
    "azobenzene_derivative",
    "azobenzene_explicit",
    "azobenzene_isomerism",
    "azobenzene_numbering",
    "dihedral",
    "energy_levels",
    "spectrum_lines",
    "spectrum_bands",
    "energy_profile",
    "photoswitch",
    "substituent_effects",
)


def render(output_dir=None, formats=("svg",)):
    for module in FIGURES:
        import_module(module).render(output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
