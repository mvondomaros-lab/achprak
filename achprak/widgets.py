import time

import IPython.display
import ipywidgets as widgets
import nglview


class NGLAccordion:
    """
    An NGL view wrapped inside and ipywidgets Accordion.

    Handles drawing upon opening the accordion and updating of the molecular data.
    """

    def __init__(self, title="3D-Struktur"):
        self.ngl_view = nglview.NGLWidget()
        self.accordion = widgets.Accordion([self.ngl_view], titles=[title])
        self.accordion.observe(self._on_open, names="selected_index")

    def show(self, output):
        with output:
            IPython.display.display(self.accordion)

    def clear(self):
        """
        Clear the NGL view.
        """
        for component in self.ngl_view:
            self.ngl_view.remove_component(component)

    def _on_open(self, change):
        """
        Called when the accordion opens. Triggers a resize.
        """
        if change["new"] == 0:
            self.ngl_view.handle_resize()

    def show_atoms(self, atoms):
        """
        Show the given ASE Atoms object in the NGL view.
        """
        self.clear()
        component = nglview.ASEStructure(atoms)
        self.ngl_view.add_component(component)
        self.ngl_view.center()

    def show_traj(self, traj):
        """
        Show the given ASE trajectory in the NGL view.
        """
        self.clear()
        trajectory = nglview.ASETrajectory(traj)
        self.ngl_view.add_trajectory(trajectory)
        self.ngl_view.center()


def flash_button(button, message):
    original = button.description
    button.disabled = True
    button.description = message
    time.sleep(0.5)
    button.description = original
    button.disabled = False
