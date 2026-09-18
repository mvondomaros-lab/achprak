"""RDKit source for azobenzene_numbering.svg, using the web app's drawing style."""

from structures import TRANS, CIS, export_structure
from style import run


def render(output_dir=None, formats=("svg",)):
    export_structure("azobenzene_numbering", TRANS, output_dir, formats, numbered=True)


if __name__ == "__main__":
    run(render, __doc__)
