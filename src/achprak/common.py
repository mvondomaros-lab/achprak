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
    rdkit.Chem.rdDetermineBonds.DetermineBonds(mol, charge=charge)
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
