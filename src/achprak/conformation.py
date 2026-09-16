"""A shared drawing scaffold and bounded preparation of starting conformers."""

from rdkit import Chem
from rdkit.Chem import AllChem, rdDepictor, rdMolTransforms


def scaffold(mol):
    """Map the ordered template core without canonicalizing equivalent sites."""
    azo = next(b for b in mol.GetBonds()
               if b.GetBeginAtom().GetSymbol() == b.GetEndAtom().GetSymbol() == "N"
               and b.GetBondType() == Chem.BondType.DOUBLE)
    nitrogens = {azo.GetBeginAtomIdx(), azo.GetEndAtomIdx()}
    indices = [a.GetIdx() for a in mol.GetAtoms()
               if a.GetIsAromatic() and a.GetSymbol() == "C" or a.GetIdx() in nitrogens]
    if len(indices) != 14:
        raise ValueError("Die Azobenzol-Grundstruktur konnte nicht zugeordnet werden.")
    configuration = "cis" if azo.GetStereo() in (Chem.BondStereo.STEREOZ, Chem.BondStereo.STEREOCIS) else "trans"
    core = Chem.MolFromSmiles("c1ccccc1/N=N" + ("\\" if configuration == "cis" else "/") + "c1ccccc1")
    rdDepictor.Compute2DCoords(core)
    return core, indices


def draw_coordinates(mol):
    """Keep ring site orientation stable when students change substituents."""
    core, indices = scaffold(mol)
    conf = core.GetConformer()
    from rdkit.Geometry import Point2D
    coords = {i: Point2D(conf.GetAtomPosition(j).x, conf.GetAtomPosition(j).y)
              for j, i in enumerate(indices)}
    rdDepictor.Compute2DCoords(mol, coordMap=coords, canonOrient=False)


def align_start(mol):
    """Prepare 3D in the drawing's ring-orientation basin; no constraints persist."""
    core, indices = scaffold(mol)
    # Ordered SMILES core: six ring carbons, N=N, six ring carbons.
    torsions = [(5, 6, 7, 8), (7, 6, 5, 0), (6, 7, 8, 9)]
    mapped = [tuple(indices[i] for i in t) for t in torsions]
    conf = mol.GetConformer()
    for source, target in zip(torsions, mapped):
        angle = rdMolTransforms.GetDihedralDeg(core.GetConformer(), *source)
        rdMolTransforms.SetDihedralDeg(conf, *target, angle)
    # Remove close contacts without allowing the rings to flip to the opposite
    # drawing orientation. These are construction restraints, not xTB restraints.
    props = AllChem.MMFFGetMoleculeProperties(mol)
    forcefield = AllChem.MMFFGetMoleculeForceField(mol, props) if props is not None else None
    if forcefield is None:
        raise RuntimeError("Für diese Startstruktur ist keine geometrische Vorbereitung verfügbar.")
    for i, torsion in enumerate(mapped):
        width = 20 if i == 0 else 45
        forcefield.MMFFAddTorsionConstraint(*torsion, True, -width, width, 100)
    forcefield.Initialize()
    forcefield.Minimize(maxIts=500)
    # Fail explicitly rather than silently showing another starting arrangement.
    for source, target in zip(torsions, mapped):
        wanted = rdMolTransforms.GetDihedralDeg(core.GetConformer(), *source)
        actual = rdMolTransforms.GetDihedralDeg(conf, *target)
        if abs((actual - wanted + 180) % 360 - 180) > 60:
            raise RuntimeError("Die gewählte Ringanordnung konnte nicht als 3D-Startstruktur erzeugt werden.")
