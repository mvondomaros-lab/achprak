import contextlib
import io

import achprak
import matplotlib.pyplot as plt
import tblite.ase
import click
import os

plt.style.use("ggplot")


def get_fname(
    conformation, r1c1, r1c2, r1c3, r1c4, r1c5, r2c1, r2c2, r2c3, r2c4, r2c5, basis, xc
):
    fname = f"uvvis_{conformation}"

    if r1c1 != "H":
        fname += f"_r1c1-{r1c1}"
    elif r1c2 != "H":
        fname += f"_r1c2-{r1c2}"
    elif r1c3 != "H":
        fname += f"_r1c3-{r1c3}"
    elif r1c4 != "H":
        fname += f"_r1c4-{r1c4}"
    elif r1c5 != "H":
        fname += f"_r1c5-{r1c5}"
    if r2c1 != "H":
        fname += f"_r2c1-{r2c1}"
    elif r2c2 != "H":
        fname += f"_r2c2-{r2c2}"
    elif r2c3 != "H":
        fname += f"_r2c3-{r2c3}"
    elif r2c4 != "H":
        fname += f"_r2c4-{r2c4}"
    elif r2c5 != "H":
        fname += f"_r2c5-{r2c5}"

    fname += f"_{xc}_{basis}.png"
    return fname


@click.command()
@click.option("--conformation", default="trans", help="Conformation.")
@click.option("--r1c1", default="H", help="Substituent R1C1.")
@click.option("--r1c2", default="H", help="Substituent R1C2.")
@click.option("--r1c3", default="H", help="Substituent R1C3.")
@click.option("--r1c4", default="H", help="Substituent R1C4.")
@click.option("--r1c5", default="H", help="Substituent R1C5.")
@click.option("--r2c1", default="H", help="Substituent R2C1.")
@click.option("--r2c2", default="H", help="Substituent R2C2.")
@click.option("--r2c3", default="H", help="Substituent R2C3.")
@click.option("--r2c4", default="H", help="Substituent R2C4.")
@click.option("--r2c5", default="H", help="Substituent R2C5.")
@click.option("--basis", default="sto-3g", help="Basis set.")
@click.option("--xc", default="lda", help="Exchange-correlation functional.")
def main(
    conformation, r1c1, r1c2, r1c3, r1c4, r1c5, r2c1, r2c2, r2c3, r2c4, r2c5, basis, xc
):
    os.makedirs("figures", exist_ok=True)

    template = achprak.azobenzene.Template(
        conformation, r1c1, r1c2, r1c3, r1c4, r1c5, r2c1, r2c2, r2c3, r2c4, r2c5
    )

    atoms = template.atoms
    atoms.calc = tblite.ase.TBLite(method="GFN1-xTB", verbosity=0)

    with contextlib.redirect_stdout(io.StringIO()):
        opt = achprak.optimization.OptMin(template.atoms)
        opt.run()

    uvvis = achprak.uvvis.UVVis(atoms)
    uvvis.calculate(basis=basis, xc=xc)

    fix, ax = plt.subplots()
    uvvis.plot(ax)
    plt.tight_layout()

    fname = get_fname(
        conformation,
        r1c1,
        r1c2,
        r1c3,
        r1c4,
        r1c5,
        r2c1,
        r2c2,
        r2c3,
        r2c4,
        r2c5,
        basis,
        xc,
    )
    plt.savefig(f"figures/{fname}", dpi=300)


if __name__ == "__main__":
    main()
