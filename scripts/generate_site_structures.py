"""Generate deterministic molecular structure assets for the teaching site."""

from pathlib import Path

from rdkit import Chem

from achprak.azobenzene import Template


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site/assets/structures/azobenzene-trans.sdf"


def main() -> None:
    molecule = Template(configuration="trans").molh
    molecule.SetProp("_Name", "trans-Azobenzol")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(Chem.MolToMolBlock(molecule).rstrip() + "\n$$$$\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
