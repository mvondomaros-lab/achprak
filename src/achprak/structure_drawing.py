"""Shared transparent RDKit drawings for the app and teaching website."""

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D

from achprak.conformation import draw_coordinates, scaffold


def structure_drawer(width, height, format="svg", panel_width=-1, panel_height=-1):
    if format not in ("svg", "png"):
        raise ValueError(f"Unsupported drawing format: {format}")
    renderer = rdMolDraw2D.MolDraw2DSVG if format == "svg" else rdMolDraw2D.MolDraw2DCairo
    drawer = renderer(width, height, panel_width, panel_height)
    drawer.drawOptions().clearBackground = False
    return drawer


def draw_structure(mol, *, width=700, height=340, explicit=False,
                   numbered=False, aromatic=False, format="svg"):
    mol = Chem.AddHs(Chem.Mol(mol)) if explicit else Chem.RemoveHs(Chem.Mol(mol))
    draw_coordinates(mol)
    drawer = structure_drawer(width, height, format)
    options = drawer.drawOptions()
    if explicit:
        for atom in mol.GetAtoms():
            options.atomLabels[atom.GetIdx()] = atom.GetSymbol()
    if numbered:
        _, indices = scaffold(mol)
        # RDKit's built-in drawing font supports ASCII primes reliably.
        for sites, suffix in (([5, 0, 1, 2, 3, 4], ""), ([8, 9, 10, 11, 12, 13], "'")):
            for number, site in enumerate(sites, 1):
                options.atomLabels[indices[site]] = f"{number}{suffix}"
    if aromatic:
        options.prepareMolsBeforeDrawing = False
        mol = rdMolDraw2D.PrepareMolForDrawing(mol, kekulize=False)
    drawer.DrawMolecule(mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()
