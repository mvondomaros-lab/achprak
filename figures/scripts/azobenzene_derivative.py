"""RDKit source for azobenzene_derivative.svg, using the web app's drawing style."""

from structures import TRANS, CIS, export_structure
from style import run


def render(output_dir=None, formats=("svg",)):
    export_structure("azobenzene_derivative", "c1c(C)c(OC)c(C)cc1/N=N/c1c(F)cc(C(F)(F)F)c(N(C)C)c1", output_dir, formats, width=900, height=440)


if __name__ == "__main__":
    run(render, __doc__)
