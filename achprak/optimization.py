import contextlib

import IPython.display
import ase.constraints
import ase.io
import ase.mep
import ase.optimize
import ase.optimize.climbfixinternals
import ase.vibrations
import clipboard
import ipywidgets
import sella


from . import common, widgets


class OptMin:
    """
    Geometry optimization.
    """

    def __init__(self, atoms, calc=None):
        self.atoms = atoms
        self.atoms.calc = calc or common.DefaultASECalculator()

    def run(self, fmax=0.01, steps=1000, output=None):
        """
        Perform a geometry optimization.
        """
        opt = ase.optimize.BFGSLineSearch(self.atoms)
        output = output or contextlib.nullcontext()
        with output:
            converged = opt.run(fmax=fmax, steps=steps)
        return converged


class OptTS:
    """
    Transition state optimization using Sella.
    """

    def __init__(self, atoms, calc=None):
        self.atoms = atoms
        self.atoms.calc = calc or common.DefaultASECalculator()

    def run(
        self,
        fmax=0.01,
        steps=1000,
        output=None,
    ):
        """
        Run Sella.
        """
        opt = sella.Sella(
            self.atoms,
            internal=True,
        )
        output = output or contextlib.nullcontext()
        with output:
            converged = opt.run(fmax=fmax, steps=steps)
        return converged


class OptToolBase:
    """
    An interactive geometry optimization tool.
    """

    _error_message = """
        Leider ist etwas schief gegangen. Bitte verändern Sie Ihre Startstruktur und versuchen Sie es noch einmal. 
        
        Sollte dieser Fehler wiederholt auftreten, kontaktieren Sie bitte Ihre Assistent*innen.
        """

    def __init__(self):
        self.atoms = None
        self.converged = False

        # Output widgets and friends.
        self._xyz_init_output = ipywidgets.Output()
        self._xyz_opt_output = ipywidgets.Output()
        self._run_output = ipywidgets.Output(layout=common.OUTPUT_LAYOUT)
        self._ngl_accordion = widgets.NGLAccordion()
        self._run_accordion = ipywidgets.Accordion(
            [self._run_output], titles=["Programmausgabe"]
        )

        # Paste button
        self._paste_button = ipywidgets.Button(description=common.PASTE_TEXT)
        self._paste_button.on_click(self._on_click)

        # Copy button
        self._copy_button = ipywidgets.Button(description=common.COPY_TEXT)
        self._copy_button.on_click(self._on_click)

    def show(self):
        IPython.display.display(
            ipywidgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_init_output,
            ipywidgets.Label("Ausgabe", style=common.LABEL_STYLE),
            self._run_accordion,
            self._ngl_accordion.accordion,
            ipywidgets.Accordion(
                [ipywidgets.VBox([self._xyz_opt_output, self._copy_button])],
                titles=["Koordinaten (XYZ-Format)"],
            ),
        )

    def _run(self):
        """
        Run the optimization. Must be implemented by subclasses. Must work with self.atoms and must set self.converged.
        """
        pass

    def _show_results(self):
        """
        Show the results of the optimization.
        """
        if self.converged:
            self._ngl_accordion.show_atoms(self.atoms)
            with self._xyz_opt_output:
                print(common.atoms_to_xyz(self.atoms))
        else:
            with self._run_output:
                print(common.atoms_to_xyz(self._error_message))

    def _clear(self):
        self._run_output.clear_output(wait=False)
        self._ngl_accordion.clear()
        self._xyz_opt_output.clear_output(wait=False)

    def _block(self):
        """
        Block further input.
        """
        self._paste_button.disabled = True
        self._run_accordion.titles = [common.RUN_TEXT]
        self._run_accordion.open()

    def _unblock(self):
        self._paste_button.disabled = False
        self._run_accordion.titles = [common.RUN_COMPLETE_TEXT]

    def _on_click(self, button):
        """
        Called when the user clicks a button.
        """
        if button is self._copy_button:
            xyz = common.atoms_to_xyz(self.atoms)
            clipboard.copy(xyz)
            widgets.flash_button(button, message=common.COPY_OK_TEXT)
        elif button is self._paste_button:
            self.atoms = common.clipboard_to_atoms(
                button=button, output=self._xyz_init_output
            )

            if self.atoms is not None:
                self._block()
                self._clear()
                self._run()
                self._show_results()
                self._unblock()

    def _on_open_ngl_accordion(self, change):
        """
        Called when the accordion holding the NGLWidget opens. Triggers a resize.
        """
        if change["new"] == 0:
            self._ngl_view.handle_resize()
