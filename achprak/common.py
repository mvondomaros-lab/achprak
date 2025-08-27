import contextlib
import io
import os
import sys
import tempfile

import ase.io
import numpy as np
import rdkit.Chem.rdDetermineBonds
import rdkit.Chem.rdmolfiles
import tblite.ase

from . import widgets
from .clipboard import clipboard

LABEL_STYLE = {"font_size": "15px", "font_weight": "bold"}
OUTPUT_LAYOUT = {"height": "250px", "overflow": "auto"}
TEXTAREA_LAYOUT = {"width": "auto", "height": "250px"}

COPY_TEXT = "Kopieren 📋"
COPY_OK_TEXT = "Kopiert ✅"
COPY_ERROR_TEXT = "Fehler ❌"

PASTE_TEXT = "Einfügen  📥"
PASTE_OK_TEXT = "Eingefügt ✅"
PASTE_ERROR_TEXT = "Ungültige Eingabe ❌"

RUN_START_TEXT = "Starten  ▶️"
RUN_RUNNING_TEXT = "Läuft  ⏳️"
RUN_OK_TEXT = "Fertig ✅"
RUN_ERROR_TEXT = "Fehler ❌"

SOLVENT_NAME = "ethanol"
SOLVENT_EPS = 24.3


class DefaultASECalculator(tblite.ase.TBLite):
    def __init__(
        self, method="GFN1-xTB", solvation=("alpb", SOLVENT_NAME), verbosity=0
    ):
        super().__init__(method=method, solvation=solvation, verbosity=verbosity)


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


def clipboard_to_atoms(button, output):
    xyz = clipboard.paste()
    try:
        atoms = xyz_to_atoms(xyz)
        with output:
            print(xyz)
        widgets.flash_button(button, message=PASTE_OK_TEXT)
        return atoms
    except Exception:
        widgets.flash_button(button, message=PASTE_ERROR_TEXT)
        return None


@contextlib.contextmanager
def nested_context(*cms):
    exits = []
    try:
        for cm in cms:
            result = cm.__enter__()
            exits.append((cm, result))
        yield exits
    finally:
        exc_info = sys.exc_info()
        for cm, _ in reversed(exits):
            cm.__exit__(*exc_info)


@contextlib.contextmanager
def tempdir():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            yield tmp
        finally:
            os.chdir(cwd)
