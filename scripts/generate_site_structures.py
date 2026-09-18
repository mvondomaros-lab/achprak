"""Generate deterministic molecular structure assets for the teaching site."""

from pathlib import Path

from rdkit import Chem

from achprak import azobenzene, common, optimization


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site/assets/structures/azobenzene-trans.sdf"


def main() -> None:
    template = azobenzene.Template(configuration="trans")
    minimum = optimization.OptMin(template.atoms)
    if not minimum.run():
        raise RuntimeError("Die Minimumsuche für trans-Azobenzol ist nicht konvergiert.")

    # Match the app's minimum-structure path, including bond perception from
    # the optimized coordinates, before publishing the result as an SDF.
    molecule = common.atoms_to_mol(minimum.atoms)
    molecule.SetProp("_Name", "trans-Azobenzol · optimierte Minimumstruktur")
    molecule.SetProp("calculation_method", "GFN1-xTB/ALPB(ethanol)")
    molecule.SetProp("optimization_fmax_ev_angstrom", str(common.MINIMUM_FMAX))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    properties = (
        ">  <calculation_method>\nGFN1-xTB/ALPB(ethanol)\n\n"
        ">  <optimization_fmax_ev_angstrom>\n"
        f"{common.MINIMUM_FMAX}\n\n"
    )
    OUTPUT.write_text(
        Chem.MolToMolBlock(molecule).rstrip() + "\n" + properties + "$$$$\n"
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
