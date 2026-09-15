import contextlib
import io

import numpy as np
import rdkit.Chem
import rdkit.Chem.AllChem

from . import common


class Template:
    """Azobenzene template with substituents on both rings."""

    substituent_smiles = {
        "H": "",
        "Me": "(C)",
        "NMe2": "(N(C)C)",
        "CF3": "(C(F)(F)F)",
        "OMe": "(O(C))",
        "F": "(F)",
        "SO2CF3": "(S(=O)(=O)C(F)(F)F)",
    }

    def __init__(
        self,
        configuration="trans",
        r1c1="H",
        r1c2="H",
        r1c3="H",
        r1c4="H",
        r1c5="H",
        r2c1="H",
        r2c2="H",
        r2c3="H",
        r2c4="H",
        r2c5="H",
    ):
        self.configuration = configuration
        self.substituents = [
            r1c1,
            r1c2,
            r1c3,
            r1c4,
            r1c5,
            r2c1,
            r2c2,
            r2c3,
            r2c4,
            r2c5,
        ]
        self.smiles = self._init_smiles()
        self.mol = self._init_mol()
        self.molh = self._init_molh()
        self.atoms = self._init_atoms()

    def _init_smiles(self) -> str:
        smiles = ["c1"]
        for carbon in range(5):
            sub = self.substituents[carbon]
            smiles.append(self.substituent_smiles[sub])
            smiles.append("c")
        smiles.append("1N=Nc2")
        for carbon in range(5):
            smiles.append("c")
            sub = self.substituents[carbon + 5]
            smiles.append(self.substituent_smiles[sub])
        smiles.append("2")
        smiles = "".join(smiles)

        smiles = smiles.replace(
            "N=N", "/N=N/" if self.configuration == "trans" else "/N=N\\"
        )
        return smiles

    def _init_mol(self) -> rdkit.Chem.Mol:
        mol = rdkit.Chem.MolFromSmiles(self.smiles)
        if mol is None:
            raise ValueError(f"Ungültige Molekülbeschreibung (SMILES): {self.smiles}")
        return mol

    def _init_molh(self) -> rdkit.Chem.Mol:
        return rdkit.Chem.AddHs(self.mol)

    def _init_atoms(self):
        mol = self.molh

        # ETKDG first, then fallback embedding.
        params = rdkit.Chem.AllChem.ETKDGv3()
        params.randomSeed = 42
        rc = rdkit.Chem.AllChem.EmbedMolecule(mol, params)
        if rc != 0:
            rc = rdkit.Chem.AllChem.EmbedMolecule(mol, randomSeed=42)
        if rc != 0:
            raise RuntimeError(
                "RDKit konnte keine 3D-Startstruktur für dieses Molekül erzeugen."
            )

        return common.mol_to_atoms(mol)


class Properties:
    """Compute selected properties of an azobenzene derivative."""

    def __init__(self, atoms):
        self.atoms = atoms
        self.atoms.calc = common.DefaultASECalculator()
        self.mol = common.atoms_to_mol(atoms)

    def _find_azo_bond(self):
        for bond in self.mol.GetBonds():
            a = bond.GetBeginAtom()
            b = bond.GetEndAtom()
            if (
                a.GetSymbol() == "N"
                and b.GetSymbol() == "N"
                and bond.GetBondType().name == "DOUBLE"
            ):
                return a.GetIdx(), b.GetIdx()
        return None

    def _find_carbon_neighbor(self, i):
        for nbr in self.mol.GetAtomWithIdx(i).GetNeighbors():
            if nbr.GetSymbol() == "C":
                return nbr.GetIdx()
        return None

    def cnnc_dihedral_indices(self):
        azo = self._find_azo_bond()
        if azo is None:
            raise ValueError(
                "In dieser Struktur wurde keine N=N-Doppelbindung gefunden."
            )
        n1, n2 = azo

        c1 = self._find_carbon_neighbor(n1)
        c2 = self._find_carbon_neighbor(n2)
        if c1 is None or c2 is None:
            raise ValueError(
                "An den Stickstoffatomen der Azogruppe wurden keine benachbarten Kohlenstoffatome gefunden."
            )

        return [c1, n1, n2, c2]

    def cnnc_dihedral(self):
        return self.atoms.get_dihedral(*self.cnnc_dihedral_indices())

    def ring_distance(self):
        rings = self.mol.GetRingInfo().AtomRings()
        if len(rings) < 2:
            raise ValueError(
                "Für die Azobenzolstruktur werden mindestens zwei Ringe benötigt."
            )
        com1 = self.atoms[rings[0]].get_center_of_mass()
        com2 = self.atoms[rings[1]].get_center_of_mass()
        return np.linalg.norm(com1 - com2) * 100.0  # pm

    def energy(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.atoms.get_potential_energy()  # eV
