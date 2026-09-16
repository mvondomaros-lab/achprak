import contextlib
import io
import os
import tempfile

import ase.io
import numpy as np
import rdkit.Chem.rdDetermineBonds
import rdkit.Chem.rdmolfiles
import tblite.ase

SOLVENT_NAME = "ethanol"
SOLVENT_EPS = 24.3

MINIMUM_FMAX = 0.002  # eV/Å; also used for endpoint connectivity checks.
OPTIMIZATION_ACCURACY = 0.1


class DefaultASECalculator(tblite.ase.TBLite):
    def __init__(
        self,
        method="GFN1-xTB",
        solvation=("alpb", SOLVENT_NAME),
        accuracy=OPTIMIZATION_ACCURACY,
        verbosity=0,
    ):
        super().__init__(
            method=method, solvation=solvation, accuracy=accuracy, verbosity=verbosity
        )


def atoms_to_xyz(atoms):
    """
    Convert an ASE Atoms object to an XYZ string.
    """
    with io.StringIO() as f:
        ase.io.write(f, atoms, format="xyz")
        f.seek(0)
        xyz = f.read()
    return xyz


def xyz_to_atoms(xyz):
    """
    Construct an ASE Atoms object from XYZ string.
    """
    f = io.StringIO(xyz)
    atoms = ase.io.read(f, format="xyz")
    return atoms


def mol_to_atoms(mol):
    """
    Convert an RDKit Mol object to an ASE Atoms object.
    """
    conf = mol.GetConformer()
    atoms = ase.Atoms(
        positions=conf.GetPositions(),
        numbers=[atom.GetAtomicNum() for atom in mol.GetAtoms()],
    )
    return atoms


def atoms_to_mol(atoms, charge=0):
    """
    Construct an RDKit Mol object from an ASE Atoms object.
    """
    with io.StringIO() as f:
        ase.io.write(f, atoms, format="xyz")
        f.seek(0)
        xyz = f.read()

    mol = rdkit.Chem.rdmolfiles.MolFromXYZBlock(xyz)
    # Distance-only perception can turn a short nonbonded S...N contact into
    # a charged covalent ring in crowded sulfonyl-substituted azobenzenes.
    # Extended Hueckel overlap distinguishes that contact from the bonds
    # used for fragment rotation and endpoint-connectivity validation.
    try:
        rdkit.Chem.rdDetermineBonds.DetermineBonds(mol, charge=charge, useHueckel=True)
    except ValueError as error:
        # RDKit can miss the charge-separated nitro resonance form and instead
        # assign two terminal oxygen radicals. Keep Hueckel connectivity, then
        # normalize ONLY that motif to [N+](=O)[O-]. Reject other radical results.
        mol = rdkit.Chem.rdmolfiles.MolFromXYZBlock(xyz)
        rdkit.Chem.rdDetermineBonds.DetermineBonds(
            mol, charge=charge, useHueckel=True, allowChargedFragments=False
        )
        repaired = False
        for atom in mol.GetAtoms():
            if atom.GetSymbol() != "N" or atom.GetDegree() != 3 or atom.GetFormalCharge() != 0:
                continue
            oxygens = [a for a in atom.GetNeighbors() if a.GetSymbol() == "O"
                       and a.GetDegree() == 1 and a.GetNumRadicalElectrons() == 1]
            if len(oxygens) != 2 or not any(a.GetSymbol() == "C" for a in atom.GetNeighbors()):
                continue
            if any(mol.GetBondBetweenAtoms(atom.GetIdx(), o.GetIdx()).GetBondType()
                   != rdkit.Chem.BondType.SINGLE for o in oxygens):
                continue
            atom.SetFormalCharge(1)
            oxygens[0].SetFormalCharge(-1)
            for oxygen in oxygens:
                oxygen.SetNumRadicalElectrons(0)
            mol.GetBondBetweenAtoms(atom.GetIdx(), oxygens[1].GetIdx()).SetBondType(rdkit.Chem.BondType.DOUBLE)
            repaired = True
        rdkit.Chem.SanitizeMol(mol)
        if not repaired or rdkit.Chem.GetFormalCharge(mol) != charge or any(
            atom.GetNumRadicalElectrons() for atom in mol.GetAtoms()
        ):
            raise error
    return mol


def gaussian(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))


@contextlib.contextmanager
def tempdir():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            yield tmp
        finally:
            os.chdir(cwd)
