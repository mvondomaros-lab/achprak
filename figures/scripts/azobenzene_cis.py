"""RDKit source for azobenzene_cis.svg, using the web app's drawing style."""

from structures import TRANS, CIS, export_structure
from style import run


def render(output_dir=None, formats=("svg",)):
    export_structure("azobenzene_cis", CIS, output_dir, formats, width=460, height=340)


if __name__ == "__main__":
    run(render, __doc__)
