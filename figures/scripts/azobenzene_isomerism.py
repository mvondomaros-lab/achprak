"""RDKit source for the light-induced cis–trans isomerization scheme."""

from pathlib import Path

from rdkit import Chem
from rdkit.Geometry import Point2D
from achprak.conformation import draw_coordinates
from achprak.structure_drawing import structure_drawer
from structures import TRANS, CIS
from style import run


def render(output_dir=None, formats=("svg",)):
    output_dir = Path(output_dir or Path(__file__).resolve().parents[1] / "drawings")
    output_dir.mkdir(parents=True, exist_ok=True)
    for extension in formats:
        drawer = structure_drawer(1100, 340, extension, 420, 280)
        drawer.drawOptions().fixedScale = 0.1
        for smiles, x in ((TRANS, 0), (CIS, 680)):
            mol = Chem.MolFromSmiles(smiles)
            draw_coordinates(mol)
            drawer.SetOffset(x, 15)
            drawer.DrawMolecule(mol)
        drawer.SetOffset(0, 0)
        drawer.SetColour((0.1, 0.18, 0.26))
        drawer.SetLineWidth(2)
        drawer.DrawArrow(Point2D(450, 145), Point2D(650, 145), rawCoords=True)
        drawer.DrawArrow(Point2D(650, 170), Point2D(450, 170), rawCoords=True)
        drawer.SetFontSize(20)
        drawer.DrawString("Licht", Point2D(550, 112), rawCoords=True)
        drawer.DrawString("trans", Point2D(210, 310), rawCoords=True)
        drawer.DrawString("cis", Point2D(890, 310), rawCoords=True)
        drawer.FinishDrawing()
        drawing = drawer.GetDrawingText()
        path = output_dir / f"azobenzene_isomerism.{extension}"
        if extension == "svg":
            path.write_text(drawing)
        else:
            path.write_bytes(drawing)


if __name__ == "__main__":
    run(render, __doc__)
