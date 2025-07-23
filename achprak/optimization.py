import contextlib
import io
import os

import IPython.display
import clipboard
import ipywidgets
import sella
import ase.optimize
import ase.vibrations
import ase.io
import tempfile
import rdkit.Chem.AllChem
import rdkit.Chem.rdMolTransforms

from . import common, widgets, azobenzene


class OptMin:
    """
    Geometry optimization.
    """

    def __init__(self, atoms, calc=None):
        self.atoms = atoms
        self.atoms.calc = calc or common.DefaultASECalculator()
        self.traj = None

    def run(self, fmax=0.01, steps=1000, output=None):
        """
        Perform a geometry optimization.
        """
        with tempfile.NamedTemporaryFile(suffix=".traj") as tmp:
            opt = ase.optimize.BFGSLineSearch(self.atoms, trajectory=tmp.name)
            output = output or contextlib.nullcontext()
            with output:
                converged = opt.run(fmax=fmax, steps=steps)
            self.traj = ase.io.read(tmp.name, index=":")
        return converged


class OptTS:
    """
    Transition state optimization using Sella.
    """

    def __init__(self, atoms, calc=None):
        # TODO: This is hardcoded for azobenzene, but should be generalized.
        # Start by setting the C-N=N-C dihedral angle to 90 degrees.
        properties = azobenzene.Properties(atoms)
        mol = properties.mol
        conf = mol.GetConformer()
        indices = properties.cnnc_dihedral_indices()
        rdkit.Chem.rdMolTransforms.SetDihedralDeg(conf, *indices, 90.0)

        # Run an optimization with MMFF94s, keeping the dihedral harmonically restrained.
        mp = rdkit.Chem.AllChem.MMFFGetMoleculeProperties(mol, mmffVariant="MMFF94s")
        ff = rdkit.Chem.AllChem.MMFFGetMoleculeForceField(mol, mp)
        ff.MMFFAddTorsionConstraint(*indices, False, 90, 90, 1.0e5)
        ff.Minimize(maxIts=10000)

        self.atoms = atoms
        self.atoms.calc = calc or common.DefaultASECalculator()
        self.traj = None

    def run(
        self,
        fmax=0.01,
        steps=1000,
        output=None,
    ):
        """
        Run Sella.
        """
        # Run the TS optimization.
        opt = sella.Sella(self.atoms, internal=True)
        output = output or contextlib.nullcontext()
        with output:
            converged = opt.run(fmax=fmax, steps=steps)

        # Make a trajectory of the lowest-energy normal mode.
        if converged:
            vibrations = ase.vibrations.Vibrations(self.atoms)
            with common.tempdir() as tmp:
                with contextlib.redirect_stdout(io.StringIO()):
                    vibrations.run()
                vibrations.write_mode(0, nimages=30, kT=0.1)
                fname = os.path.join(tmp, "vib.0.traj")
                self.traj = ase.io.Trajectory(fname)
        return converged


class OptTool:
    """
    An interactive structure optimization tool.
    """

    def __init__(self):
        self.atoms = None
        self.converged = False
        self.traj = None

        # Output widgets and friends.
        self._xyz_init_output = ipywidgets.Output()
        self._xyz_opt_output = ipywidgets.Output()
        self._run_output = ipywidgets.Output(layout=common.OUTPUT_LAYOUT)
        self._ngl_accordion = widgets.NGLAccordion(title="Trajektorie")
        self._run_output_accordion = ipywidgets.Accordion(
            [self._run_output], titles=["Programmausgabe"]
        )

        # Radio buttons for optimization target.
        self._target_buttons = ipywidgets.RadioButtons(
            options=["Minimum", "Übergangszustand"], orientation="horizontal"
        )

        # Paste button
        self._paste_button = ipywidgets.Button(description=common.PASTE_TEXT)
        self._paste_button.on_click(self._on_click)

        # Run Button
        self._run_button = ipywidgets.Button(description=common.RUN_START_TEXT)
        self._run_button.on_click(self._on_click)

        # Copy button
        self._copy_button = ipywidgets.Button(description=common.COPY_TEXT)
        self._copy_button.on_click(self._on_click)

    def show(self):
        IPython.display.display(
            ipywidgets.Label("Zielstruktur", style=common.LABEL_STYLE),
            self._target_buttons,
            ipywidgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_init_output,
            ipywidgets.Label("Berechnung", style=common.LABEL_STYLE),
            self._run_button,
            self._run_output_accordion,
            self._ngl_accordion.accordion,
            ipywidgets.Accordion(
                [ipywidgets.VBox([self._xyz_opt_output, self._copy_button])],
                titles=["Koordinaten (XYZ-Format)"],
            ),
        )

    def _on_click(self, button):
        """
        Called when the user clicks a button.
        """
        if button is self._paste_button:
            self._reset()
            self.atoms = common.clipboard_to_atoms(
                button=button, output=self._xyz_init_output
            )
            if self.atoms is not None:
                self._run_button.disabled = False
        elif button is self._run_button:
            self._run_button.disabled = True
            self._run_button.description = common.RUN_RUNNING_TEXT
            self._run()
            if self.converged:
                self._run_button.description = common.RUN_OK_TEXT
            else:
                self._run_button.description = common.RUN_ERROR_TEXT
            self._update()
            self._run_button.disabled = False
        elif button is self._copy_button:
            xyz = common.atoms_to_xyz(self.atoms)
            clipboard.copy(xyz)
            widgets.flash_button(button, message=common.COPY_OK_TEXT)

    def _reset(self):
        self._run_output.clear_output()
        self._ngl_accordion.clear()
        self._xyz_opt_output.clear_output()
        self.atoms = None
        self.converged = False
        self.traj = None
        self._xyz_init_output.clear_output()
        self._run_button.disabled = True
        self._run_button.description = common.RUN_START_TEXT

    def _run(self):
        """
        Run the optimization.
        """
        if self._target_buttons.value == "Minimum":
            opt = OptMin(self.atoms)
        else:
            opt = OptTS(self.atoms)

        # Supper annoying hack, because TBLite does not respect its own verbosity setting.
        output = common.nested_context(
            self._run_output, contextlib.redirect_stdout(io.StringIO())
        )
        self.converged = opt.run(output=output)
        self.atoms = opt.atoms
        self.traj = opt.traj

    def _update(self):
        """
        Show the results of the optimization.
        """
        self._ngl_accordion.show_traj(self.traj)
        with self._xyz_opt_output:
            print(common.atoms_to_xyz(self.atoms))
