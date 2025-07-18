import contextlib
import io
import sys

import IPython.display
import ase.io
import clipboard
import rdkit.Chem.rdDetermineBonds
import rdkit.Chem.rdmolfiles
import pyscf.gto
import numpy as np
import tblite.ase

from . import widgets

LABEL_STYLE = {"font_size": "15px", "font_weight": "bold"}
OUTPUT_LAYOUT = {"height": "250px", "overflow": "auto"}
TEXTAREA_LAYOUT = {"width": "auto", "height": "250px"}

COPY_TEXT = "Kopieren 📋"
COPY_OK_TEXT = "Kopiert ✅"
COPY_ERROR_TEXT = "Fehler ❌"
PASTE_TEXT = "Einfügen  📥"
PASTE_OK_TEXT = "Eingefügt ✅"
PASTE_ERROR_TEXT = "Ungültige Eingabe ❌"
RUN_TEXT = "Programmausgabe ⏳"
RUN_COMPLETE_TEXT = "Programmausgabe ✅"

SOLVENT_NAME = "methanol"
SOLVENT_EPS = 32.66


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


def atoms_to_pyscf(atoms):
    atom_list = []
    for element, position in zip(atoms.get_chemical_symbols(), atoms.get_positions()):
        atom_list.append((element, position))
    mol = pyscf.gto.Mole()
    mol.atom = atom_list
    mol.unit = "Angstrom"
    return mol


def gaussian(x, mu, sigma):
    return np.exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))


def clipboard_to_atoms(button, output):
    xyz = clipboard.paste()
    try:
        atoms = xyz_to_atoms(xyz)
        with output:
            IPython.display.clear_output(wait=True)
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
