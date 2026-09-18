"""RDKit source for azobenzene_explicit.svg, using the web app's drawing style."""

from structures import TRANS, CIS, export_structure
from style import run


def render(output_dir=None, formats=("svg",)):
    export_structure("azobenzene_explicit", TRANS, output_dir, formats, explicit=True, width=760, height=420)


if __name__ == "__main__":
    run(render, __doc__)
