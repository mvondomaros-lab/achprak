"""RDKit source for azobenzene_4_methoxy.svg, using the web app's drawing style."""

from structures import TRANS, CIS, export_structure
from style import run


def render(output_dir=None, formats=("svg",)):
    export_structure("azobenzene_4_methoxy", "c1cc(OC)ccc1/N=N/c1ccccc1", output_dir, formats)


if __name__ == "__main__":
    run(render, __doc__)
