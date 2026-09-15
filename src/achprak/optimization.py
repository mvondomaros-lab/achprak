import contextlib
import tempfile

import IPython.display
import ase.io
import ipywidgets
import sella

from . import common, ui
from .transition_state import OptTS
from .clipboard import clipboard


class OptMin:
    """
    Geometry optimization.
    """

    def __init__(self, atoms, calc=None):
        self.atoms = atoms
        self.atoms.calc = calc or common.DefaultASECalculator(
            accuracy=common.OPTIMIZATION_ACCURACY
        )
        self.traj = None

    def run(self, output=None, steps=500, observer=None):
        """
        Perform a geometry optimization.
        """
        with tempfile.NamedTemporaryFile(suffix=".traj") as tmp:
            opt = sella.Sella(self.atoms, order=0, internal=True, trajectory=tmp.name)
            if observer is not None:
                opt.attach(lambda: observer(self.atoms, opt.nsteps, "optimization"))
            output = output or contextlib.nullcontext()
            with output:
                converged = opt.run(fmax=common.MINIMUM_FMAX, steps=steps)
            self.traj = ase.io.read(tmp.name, index=":")
        return converged


class OptTool:
    """
    An interactive structure optimization tool.
    """

    def __init__(self):
        self.atoms = None
        self.converged = False
        self.opt = None
        self.traj = None

        # Output widgets and friends.
        self._xyz_init_output = ipywidgets.Output()
        self._xyz_opt_output = ipywidgets.Output()
        self._run_output = ipywidgets.Output(layout=common.OUTPUT_LAYOUT)
        self._ngl_accordion = ui.NGLAccordion(title="Trajektorie")
        self._run_output_accordion = ipywidgets.Accordion(
            [self._run_output], titles=["Programmausgabe"]
        )

        # Radio buttons for optimization target.
        self._target_buttons = ipywidgets.RadioButtons(
            options=["Minimum", "Übergangszustand"], orientation="horizontal"
        )
        self._target_buttons.observe(self._on_change, names="value")

        # Paste button
        self._paste_button = ipywidgets.Button(description=common.PASTE_TEXT)
        self._paste_button.on_click(self._on_click)

        # Run Button
        self._run_button = ipywidgets.Button(
            description=common.RUN_START_TEXT, disabled=True
        )
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
        elif button is self._copy_button:
            xyz = common.atoms_to_xyz(self.atoms)
            clipboard.copy(xyz)
            ui.flash_button(button, message=common.COPY_OK_TEXT)

    def _on_change(self, change):
        if change["type"] == "change" and change["name"] == "value":
            self._reset()

    def _reset(self):
        self._xyz_init_output.clear_output()
        self._run_output.clear_output()
        self._ngl_accordion.clear()
        self._xyz_opt_output.clear_output()
        self.atoms = None
        self.converged = False
        self.opt = None
        self.traj = None

        self._run_button.disabled = True
        self._run_button.description = common.RUN_START_TEXT

    def _run(self):
        """
        Run the optimization.
        """
        if self._target_buttons.value == "Minimum":
            self.opt = OptMin(self.atoms)
        else:
            self.opt = OptTS(self.atoms)

        self.converged = self.opt.run(output=self._run_output)
        self.atoms = self.opt.atoms
        self.traj = self.opt.traj

    def _update(self):
        """
        Show the results of the optimization.
        """
        self._ngl_accordion.show_traj(self.traj)
        with self._xyz_opt_output:
            print(common.atoms_to_xyz(self.atoms))
