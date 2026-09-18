"""RDKit source for 4-methoxy-4'-nitroazobenzene, using the web app's drawing style."""

from structures import export_structure
from style import run


def render(output_dir=None, formats=("svg",)):
    export_structure(
        "azobenzene_4_methoxy_4_prime_nitro",
        "c1cc(OC)ccc1/N=N/c1ccc([N+](=O)[O-])cc1",
        output_dir,
        formats,
        rotate=11,
    )


if __name__ == "__main__":
    run(render, __doc__)
