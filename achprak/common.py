import contextlib
import io
import re
import sys
import time

import IPython.display
import ase.io
import clipboard
import rdkit.Chem.rdDetermineBonds
import rdkit.Chem.rdmolfiles

LABEL_STYLE = {"font_size": "15px", "font_weight": "bold"}
OUTPUT_LAYOUT = {"height": "250px", "overflow": "auto"}
TEXTAREA_LAYOUT = {"width": "auto", "height": "250px"}


def valid_xyz(s: str) -> bool:
    """
    Checks if the provided string `s` is a valid XYZ file format.

    XYZ format:
    - First line: integer N, the number of atoms.
    - Second line: comment (ignored).
    - Next N lines: element symbol and three floating-point coordinates.

    Returns True if valid, False otherwise.
    """
    lines = s.strip().splitlines()
    # Must have at least 3 lines: count, comment, at least one atom.
    if len(lines) < 3:
        return False

    # First line must be integer count matching number of atom lines.
    try:
        n_atoms = int(lines[0])
    except ValueError:
        return False
    if n_atoms != len(lines) - 2:
        return False

    # Validate each atom line
    for atom_line in lines[2:]:
        parts = atom_line.split()
        if len(parts) != 4:
            return False
        symbol, x_str, y_str, z_str = parts
        # Atom symbol: letters only
        if not re.fullmatch(r"[A-Za-z]+", symbol):
            return False
        # Coordinates: valid floats
        try:
            float(x_str)
            float(y_str)
            float(z_str)
        except ValueError:
            return False

    return True


def atoms_to_xyz(atoms):
    """
    Convert an ASE Atoms object to an XYZ string.
    """
    f = io.StringIO()
    atoms.write(f, format="xyz")
    return f.getvalue()


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


def flash_button(button, message):
    original = button.description
    button.disabled = True
    button.description = message
    time.sleep(0.5)
    button.description = original
    button.disabled = False


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


def paste_xyz(output, button):
    xyz = clipboard.paste()
    valid = valid_xyz(xyz)
    if valid:
        with output:
            IPython.display.clear_output(wait=True)
            print(xyz)
        flash_button(button, "Eingefügt ✅")
        atoms = xyz_to_atoms(xyz)
        return atoms
    else:
        flash_button(button, "Ungültige Eingabe ❌")
        return None
