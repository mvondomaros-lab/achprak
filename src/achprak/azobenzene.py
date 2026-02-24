import contextlib
import io

import IPython.display
import ipywidgets
import numpy as np
import rdkit.Chem
import rdkit.Chem.AllChem
import scipy.constants

from . import common, ui
from .clipboard import clipboard


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
            raise ValueError(f"Invalid SMILES generated: {self.smiles}")
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
            raise RuntimeError("RDKit 3D embedding failed for generated molecule.")

        return common.mol_to_atoms(mol)


class TemplateTool:
    """Interactive tool for creating an azobenzene template."""

    def __init__(self):
        self.template = Template()

        self._configuration_buttons = ipywidgets.RadioButtons(
            options=["trans", "cis"],
            value=self.template.configuration,
            orientation="horizontal",
        )
        self._configuration_buttons.observe(self._on_change, names="value")

        self._substituent_dropdowns = []
        for ring in range(2):
            for carbon in range(5):
                description = f"C{carbon + 2}:" if ring == 0 else f"C{carbon + 2}':"
                dropdown = ipywidgets.Dropdown(
                    options=list(Template.substituent_smiles.keys()),
                    value=self.template.substituents[ring * 5 + carbon],
                    description=description,
                    layout={"width": "max-content"},
                )
                dropdown.observe(self._on_change, names="value")
                self._substituent_dropdowns.append(dropdown)

        self._mol_output = ipywidgets.Output()
        self._xyz_output = ipywidgets.Output()

        self._copy_button = ipywidgets.Button(description=common.COPY_TEXT)
        self._copy_button.on_click(self._on_click)

    def show(self):
        IPython.display.display(
            ipywidgets.Label("Konfiguration", style=common.LABEL_STYLE),
            self._configuration_buttons,
            ipywidgets.Label("Substituenten am ersten Ring", style=common.LABEL_STYLE),
            ipywidgets.HBox(self._substituent_dropdowns[:5]),
            ipywidgets.Label("Substituenten am zweiten Ring", style=common.LABEL_STYLE),
            ipywidgets.HBox(self._substituent_dropdowns[5:]),
            ipywidgets.Label("2D-Struktur", style=common.LABEL_STYLE),
            self._mol_output,
            ipywidgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._xyz_output,
            self._copy_button,
        )

        with self._mol_output:
            IPython.display.display(self.template.mol)

        with self._xyz_output:
            self.template.atoms.write("-", format="xyz")

    def _on_change(self, change):
        if change.get("type") == "change" and change.get("name") == "value":
            self._update_template()

            with self._mol_output:
                IPython.display.clear_output(wait=True)
                IPython.display.display(self.template.mol)

            with self._xyz_output:
                IPython.display.clear_output(wait=True)
                self.template.atoms.write("-", format="xyz")

    def _update_template(self):
        kwargs = {"configuration": self._configuration_buttons.value}
        for ring in range(2):
            for carbon in range(5):
                key = f"r{ring + 1}c{carbon + 1}"
                kwargs[key] = self._substituent_dropdowns[ring * 5 + carbon].value
        self.template = Template(**kwargs)

    def _on_click(self, button):
        if button is self._copy_button:
            xyz = common.atoms_to_xyz(self.template.atoms)
            clipboard.copy(xyz)
            ui.flash_button(button, message=common.COPY_OK_TEXT)


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
            raise ValueError("Could not find azo N=N double bond in molecule.")
        n1, n2 = azo

        c1 = self._find_carbon_neighbor(n1)
        c2 = self._find_carbon_neighbor(n2)
        if c1 is None or c2 is None:
            raise ValueError(
                "Could not find carbon neighbors adjacent to azo nitrogens."
            )

        return [c1, n1, n2, c2]

    def cnnc_dihedral(self):
        return self.atoms.get_dihedral(*self.cnnc_dihedral_indices())

    def ring_distance(self):
        rings = self.mol.GetRingInfo().AtomRings()
        if len(rings) < 2:
            raise ValueError("Expected at least two rings in azobenzene.")
        com1 = self.atoms[rings[0]].get_center_of_mass()
        com2 = self.atoms[rings[1]].get_center_of_mass()
        return np.linalg.norm(com1 - com2) * 100.0  # pm

    def energy(self):
        with contextlib.redirect_stdout(io.StringIO()):
            energy = self.atoms.get_potential_energy()  # eV
        return energy * scipy.constants.eV * scipy.constants.N_A / 1000.0  # kJ/mol


class PropertiesTool:
    """Interactive tool for visualization and property calculation."""

    def __init__(self):
        self.atoms = None
        self.properties = None

        self._xyz_output = ipywidgets.Output()
        self._ngl_accordion = ui.NGLAccordion()

        self._paste_button = ipywidgets.Button(description=common.PASTE_TEXT)
        self._paste_button.on_click(self._on_click)

        self._run_button = ipywidgets.Button(
            description=common.RUN_START_TEXT, disabled=True
        )
        self._run_button.on_click(self._on_click)

        self._energy_text = ipywidgets.Text(disabled=True)
        self._cnnc_dihedral_text = ipywidgets.Text(disabled=True)
        self._ring_distance_text = ipywidgets.Text(disabled=True)

    def show(self):
        IPython.display.display(
            ipywidgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_output,
            self._ngl_accordion.accordion,
            ipywidgets.Label("Berechnung", style=common.LABEL_STYLE),
            self._run_button,
            *[
                ipywidgets.Accordion(
                    [ipywidgets.HBox([text, ipywidgets.Label(unit)])],
                    titles=[title],
                )
                for title, text, unit in [
                    ("Energie", self._energy_text, " kJ/mol"),
                    ("Diederwinkel (C-N=N-C)", self._cnnc_dihedral_text, " °"),
                    ("Ringabstand", self._ring_distance_text, " pm"),
                ]
            ],
        )

    def _reset(self):
        self.atoms = None
        self.properties = None
        self._xyz_output.clear_output()
        self._ngl_accordion.clear()

        self._energy_text.value = ""
        self._cnnc_dihedral_text.value = ""
        self._ring_distance_text.value = ""

        self._run_button.disabled = True
        self._run_button.description = common.RUN_START_TEXT

    def _on_click(self, button):
        if button is self._paste_button:
            self._reset()
            self.atoms = common.clipboard_to_atoms(
                button=button, output=self._xyz_output
            )
            if self.atoms is not None:
                self._ngl_accordion.show_atoms(self.atoms)
                self._run_button.disabled = False

        elif button is self._run_button:
            self._run_button.disabled = True
            self._run_button.description = common.RUN_START_TEXT + "…"
            try:
                self.properties = Properties(self.atoms)
                self._update()
                self._run_button.description = common.RUN_OK_TEXT
            finally:
                self._run_button.disabled = False

    def _update(self):
        self._energy_text.value = f"{self.properties.energy():.1f}"
        self._cnnc_dihedral_text.value = f"{self.properties.cnnc_dihedral():.1f}"
        self._ring_distance_text.value = f"{self.properties.ring_distance():.1f}"
