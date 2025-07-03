import contextlib

import IPython.display
import ase.constraints
import ase.io
import ase.mep
import ase.optimize
import ase.optimize.climbfixinternals
import ase.vibrations
import clipboard
import ipywidgets as widgets
import nglview
import sella

from . import common


class OptMin:
    """
    Geometry optimization.
    """

    def __init__(self, atoms):
        self.atoms = atoms

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

    def __init__(self, atoms):
        self.atoms = atoms

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
        self._xyz_input = widgets.Output()
        self._xyz_output = widgets.Output()
        self._run_output = widgets.Output(layout=common.OUTPUT_LAYOUT)
        self._ngl_view = nglview.NGLWidget()
        self._ngl_accordion = widgets.Accordion(
            [self._ngl_view], titles=["3D-Struktur"]
        )
        self._ngl_accordion.observe(self._on_open_ngl_accordion, names="selected_index")
        self._run_accordion = widgets.Accordion(
            [self._run_output], titles=["Programmausgabe"]
        )

        # Paste button
        self._paste_button = widgets.Button(description="Einfügen 📥")
        self._paste_button.on_click(self._on_click)

        # Copy button
        self._copy_button = widgets.Button(description="Kopieren 📋")
        self._copy_button.on_click(self._on_click)

    def show(self):
        IPython.display.display(
            widgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_input,
            widgets.Label("Ausgabe", style=common.LABEL_STYLE),
            self._run_accordion,
            self._ngl_accordion,
            widgets.Accordion(
                [widgets.VBox([self._xyz_output, self._copy_button])],
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
            component = nglview.ASEStructure(self.atoms)
            self._ngl_view.add_component(component)
            with self._xyz_output:
                print(common.atoms_to_xyz(self.atoms))
        else:
            with self._run_output:
                print(common.atoms_to_xyz(self._error_message))

    def _clear(self):
        self._run_output.clear_output(wait=False)
        for component in self._ngl_view:
            self._ngl_view.remove_component(component)
        self._xyz_output.clear_output(wait=False)

    def _block(self):
        """
        Block further input.
        """
        self._paste_button.disabled = True
        self._run_accordion.titles = ["Programmausgabe ⏳"]
        self._run_accordion.open()

    def _unblock(self):
        self._paste_button.disabled = False
        self._run_accordion.titles = ["Programmausgabe"]

    def _on_click(self, button):
        """
        Called when the user clicks a button.
        """
        if button is self._copy_button:
            clipboard.copy(common.atoms_to_xyz(self.atoms))
            common.flash_button(button, "Kopiert ✅")
        elif button is self._paste_button:
            self.atoms = common.paste_xyz(self._xyz_input, self._paste_button)
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
