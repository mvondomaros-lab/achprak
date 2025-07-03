import contextlib
import io

import IPython.display
import clipboard
import ipywidgets as widgets
import nglview
import numpy as np
import rdkit.Chem.AllChem
import rdkit.Chem.rdMolTransforms
import scipy.constants
import tblite.ase

from . import common, optimization


class Template:
    """
    An azobenzene template with potential substituents in the ortho, meta, and para positions of the rings.
    """

    # Mapping from substituent labels to partial smiles strings.
    substituent_smiles = {
        "H": "",
        "F": "(F)",
        "Cl": "(Cl)",
        "OH": "(O)",
        "NH2": "(N)",
        "NMe2": "(N(C)C)",
        "NO2": "(N(=O)=O)",
        "OMe": "(OC)",
    }

    def __init__(
        self,
        conformation="trans",
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
        self.conformation = conformation
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
        self.atoms = self._init_atoms()
        self.xyz = self._init_xyz()

    def _init_smiles(self):
        """
        Construct the SMILES string of the azobenzene derivative.
        """
        # Generate SMILES with substituents.
        smiles = ["c1"]
        for carbon in range(5):
            substituent = self.substituents[carbon]
            smiles.append(self.substituent_smiles[substituent])
            smiles.append("c")
        smiles.append("1N=Nc2")
        for carbon in range(5):
            smiles.append("c")
            substituent = self.substituents[carbon + 5]
            smiles.append(self.substituent_smiles[substituent])
        smiles.append("2")
        smiles = "".join(smiles)

        # Patch the double bond conformation.
        if self.conformation == "trans":
            smiles = smiles.replace("N=N", "/N=N/")
        else:
            smiles = smiles.replace("N=N", "/N=N\\")

        return smiles

    def _init_mol(self):
        """
        Construct an RDKit Mol object.
        """
        mol = rdkit.Chem.MolFromSmiles(self.smiles)
        return mol

    def _init_atoms(self):
        """
        Construct an ASE Atoms object.
        """
        # Add Hydrogen atoms and embed the molecule.
        mol = rdkit.Chem.AddHs(self.mol)
        rdkit.Chem.AllChem.EmbedMolecule(mol)

        # Convert from rdkit to ase.
        atoms = common.mol_to_atoms(mol)

        return atoms

    def _init_xyz(self):
        """
        Construct an XYZ string.
        """
        f = io.StringIO()
        self.atoms.write(f, format="xyz")
        return f.getvalue()


class TemplateTool:
    """
    An interactive tool for creating an azobenzene template.
    """

    def __init__(self):
        self.template = Template()

        # Radio buttons for switching between conformations
        self._conformation_buttons = widgets.RadioButtons(
            options=["trans", "cis"],
            value=self.template.conformation,
            orientation="horizontal",
        )
        self._conformation_buttons.observe(self._on_change, names="value")

        # Dropdowns for changing substituents
        self._substituent_dropdowns = []
        carbon_names = ["ortho", "meta", "para", "meta", "ortho"]
        for ring in range(2):
            for carbon in range(5):
                dropdown = widgets.Dropdown(
                    options=Template.substituent_smiles.keys(),
                    value=self.template.substituents[ring * 5 + carbon],
                    description=f"C{carbon + 1} ({carbon_names[carbon]}):",
                    layout={"width": "max-content"},
                )
                dropdown.observe(self._on_change, names="value")
                self._substituent_dropdowns.append(dropdown)

        # Output widgets and friends.
        self._mol_output = widgets.Output()
        self._ngl_view = nglview.NGLWidget()
        self._ngl_accordion = widgets.Accordion(
            [self._ngl_view], titles=["3D-Struktur"]
        )
        self._ngl_accordion.observe(self._on_open_ngl_accordion, names="selected_index")
        self._xyz_output = widgets.Output()

        # Copy button
        self._copy_button = widgets.Button(description="Kopieren 📋")
        self._copy_button.on_click(self._on_click)

    def _update_template(self):
        """
        Update the template object.
        """
        kwargs = {"conformation": self._conformation_buttons.value}
        for ring in range(2):
            for carbon in range(5):
                key = f"r{ring + 1}c{carbon + 1}"
                value = self._substituent_dropdowns[ring * 5 + carbon].value
                kwargs[key] = value
        self.template = Template(**kwargs)

    def show(self):
        """
        Show the tool.
        """
        IPython.display.display(
            widgets.Label("Konformation", style=common.LABEL_STYLE),
            self._conformation_buttons,
            widgets.Label("Substituenten am ersten Ring", style=common.LABEL_STYLE),
            widgets.HBox(self._substituent_dropdowns[:5]),
            widgets.Label("Substituenten am zweiten Ring", style=common.LABEL_STYLE),
            widgets.HBox(self._substituent_dropdowns[5:]),
            widgets.Label("2D-Struktur", style=common.LABEL_STYLE),
            self._mol_output,
            widgets.Label("Ausgabe", style=common.LABEL_STYLE),
            self._ngl_accordion,
            widgets.Accordion(
                [widgets.VBox([self._xyz_output, self._copy_button])],
                titles=["Koordinaten (XYZ-Format)"],
            ),
        )
        with self._mol_output:
            IPython.display.display(self.template.mol)

        component = nglview.ASEStructure(self.template.atoms)
        self._ngl_view.add_component(component)

        with self._xyz_output:
            print(self.template.xyz)

    def _on_change(self, change):
        """
        Called when a selection widget is changed.
        """
        if change["type"] == "change" and change["name"] == "value":
            self._update_template()

            with self._mol_output:
                IPython.display.clear_output(wait=True)
                IPython.display.display(self.template.mol)

            for component in self._ngl_view:
                self._ngl_view.remove_component(component)
            component = nglview.ASEStructure(self.template.atoms)
            self._ngl_view.add_component(component)

            with self._xyz_output:
                IPython.display.clear_output(wait=True)
                print(self.template.xyz)

    def _on_click(self, button):
        """
        Called when the user clicks a button.
        """
        if button is self._copy_button:
            clipboard.copy(self.template.xyz)
            common.flash_button(button, "Kopiert ✅")

    def _on_open_ngl_accordion(self, change):
        """
        Called when the accordion holding the NGLWidget opens. Triggers a resize.
        """
        if change["new"] == 0:
            self._ngl_view.handle_resize()


class Properties:
    """
    Compute selected properties of an azobenzene derivative.
    """

    def __init__(self, atoms):
        self.atoms = atoms
        self.atoms.calc = tblite.ase.TBLite(method="GFN1-xTB", verbosity=0)
        self.mol = common.atoms_to_mol(atoms)

    def _find_azo_bond(self):
        """
        Return the indices of the azo bond nitrogen atoms.
        """
        for bond in self.mol.GetBonds():
            i, j = bond.GetBeginAtom(), bond.GetEndAtom()
            if {i.GetSymbol(), j.GetSymbol()} == {
                "N"
            } and bond.GetBondType().name == "DOUBLE":
                n1, n2 = i.GetIdx(), j.GetIdx()
                return n1, n2

    def _find_carbon_neighbor(self, i):
        """
        Find the next carbon neighbor atom of the i'th atom.
        """
        for j in self.mol.GetAtomWithIdx(i).GetNeighbors():
            if j.GetSymbol() == "C":
                return j.GetIdx()

    def cnnc_dihedral_indices(self):
        """
        Return the indices of the C-N=N-C dihedral angle.
        """
        n1, n2 = self._find_azo_bond()
        c1 = self._find_carbon_neighbor(n1)
        c2 = self._find_carbon_neighbor(n2)
        return [c1, n1, n2, c2]

    def cnnc_dihedral(self):
        """
        Return the CN=NC dihedral angle.
        """
        indices = self.cnnc_dihedral_indices()
        dihedral = self.atoms.get_dihedral(*indices)
        return dihedral

    def ring_distance(self):
        """
        Compute the center-of-mass distance between the rings.
        """
        ring_info = self.mol.GetRingInfo()
        rings = ring_info.AtomRings()
        com1 = self.atoms[rings[0]].get_center_of_mass()
        com2 = self.atoms[rings[1]].get_center_of_mass()
        distance = np.linalg.norm(com1 - com2)  # Angstrom
        distance *= 100.0  # pm
        return distance

    def energy(self):
        """
        Return the energy of the molecule.
        """
        # Discard stdout, because TBLite does not respect its own verbosity setting.
        with contextlib.redirect_stdout(io.StringIO()):
            energy = self.atoms.get_potential_energy()  # eV
        energy *= scipy.constants.eV * scipy.constants.N_A / 1000.0  # kJ/mol
        return energy


class PropertiesTool:
    """
    An interactive tool for visualization and property calculation.
    """

    def __init__(self):
        # Output widgets and friends.
        self._xyz_input = widgets.Output()

        # Paste button
        self._paste_button = widgets.Button(description="Einfügen  📥")
        self._paste_button.on_click(self._on_click)

        # Text widgets for displaying molecular properties.
        self._energy_text = widgets.Text(disabled=True)
        self._cnnc_dihedral_text = widgets.Text(disabled=True)
        self._ring_distance_text = widgets.Text(disabled=True)

    def show(self):
        """
        Show the tool.
        """
        IPython.display.display(
            widgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_input,
            widgets.Label("Ausgabe", style=common.LABEL_STYLE),
            *[
                widgets.Accordion(
                    [widgets.HBox([text, widgets.Label(unit)])], titles=[title]
                )
                for title, text, unit in [
                    ("Energie", self._energy_text, " kJ/mol"),
                    ("Diederwinkel (C-N=N-C)", self._cnnc_dihedral_text, " °"),
                    ("Ringabstand", self._ring_distance_text, " pm"),
                ]
            ],
        )

    def _on_click(self, button):
        """
        Called when buttons are clicked.
        """
        if button is self._paste_button:
            atoms = common.paste_xyz(self._xyz_input, self._paste_button)
            if atoms is not None:
                properties = Properties(atoms)
                self._update_properties(properties)

    def _update_properties(self, properties):
        self._energy_text.value = f"{properties.energy():.1f}"
        self._cnnc_dihedral_text.value = f"{properties.cnnc_dihedral():.1f}"
        self._ring_distance_text.value = f"{properties.ring_distance():.1f}"


class OptMinTool(optimization.OptToolBase):
    def _run(self):
        """
        Run the optimization.
        """
        self.atoms.calc = tblite.ase.TBLite(method="GFN1-xTB", verbosity=0)
        opt = optimization.OptMin(self.atoms)
        # Supper annoying hack, because TBLite does not respect its own verbosity setting.
        output = common.nested_context(
            self._run_output, contextlib.redirect_stdout(io.StringIO())
        )
        self.converged = opt.run(output=output)


class OptTSTool(optimization.OptToolBase):
    def _run(self):
        """
        Run the optimization.
        """
        # Start by setting the C-N=N-C dihedral angle to 90 degrees.
        properties = Properties(self.atoms)
        mol = properties.mol
        conf = mol.GetConformer()
        indices = properties.cnnc_dihedral_indices()
        rdkit.Chem.rdMolTransforms.SetDihedralDeg(conf, *indices, 90.0)

        # Run an optimization with MMFF94s, keeping the dihedral harmonically restrained.
        mp = rdkit.Chem.AllChem.MMFFGetMoleculeProperties(mol, mmffVariant="MMFF94s")
        ff = rdkit.Chem.AllChem.MMFFGetMoleculeForceField(mol, mp)
        ff.MMFFAddTorsionConstraint(*indices, False, 90, 90, 1.0e5)
        ff.Minimize(maxIts=10000)

        # Run a transition state search with Sella and GFN1-XTB.
        self.atoms = common.mol_to_atoms(mol)
        self.atoms.calc = tblite.ase.TBLite(method="GFN1-xTB", verbosity=0)
        opt = optimization.OptTS(self.atoms)
        # Supper annoying hack, because TBLite does not respect its own verbosity setting.
        output = common.nested_context(
            self._run_output, contextlib.redirect_stdout(io.StringIO())
        )
        self.converged = opt.run(output=output)
