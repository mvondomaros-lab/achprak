"""Export helpers for individually sourced RDKit structure illustrations."""

from pathlib import Path
from rdkit import Chem
from achprak.structure_drawing import draw_structure

TRANS = "c1ccccc1/N=N/c1ccccc1"
CIS = "c1ccccc1/N=N\\c1ccccc1"


def export_structure(name, smiles, output_dir=None, formats=("svg",), **options):
    output_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "drawings")
    output_dir.mkdir(parents=True, exist_ok=True)
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid structure: {smiles}")
    options.setdefault("scale_bond_width", True)
    for extension in formats:
        drawing = draw_structure(mol, format=extension, **options)
        path = output_dir / f"{name}.{extension}"
        if extension == "svg":
            path.write_text(drawing)
        else:
            path.write_bytes(drawing)
