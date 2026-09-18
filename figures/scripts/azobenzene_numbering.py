"""RDKit source for azobenzene_numbering.svg, using the web app's drawing style."""

from structures import TRANS, CIS, export_structure
from style import run


def render(output_dir=None, formats=("svg",)):
    export_structure(
        "azobenzene_numbering",
        TRANS,
        output_dir,
        formats,
        numbered=True,
        scale_bond_width=False,
        bond_line_width=2.5,
    )


if __name__ == "__main__":
    run(render, __doc__)
