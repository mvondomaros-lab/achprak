import time

from . import common

import numpy as np
import pyscf.dft
import pyscf.tddft
import pyscf.geomopt.berny_solver

import ipywidgets as widgets
import IPython.display
import matplotlib.pyplot as plt
import scipy.constants as const


class UVVis:
    """
    Compute a UV-Vis spectrum.
    """

    def __init__(self, atoms):
        self.mol = common.atoms_to_pyscf(atoms)

        self.energy = None
        self.mf = None
        self.td = None

    def calculate(self, basis="def2-TZVP", xc="BLYP", nstates=5):
        self.mol.basis = basis
        self.mol = self.mol.build()

        self.mf = pyscf.dft.RKS(self.mol).density_fit()
        self.mf.xc = xc
        self.mf.verbose = 4
        self.mf.kernel()

        self.td = pyscf.tddft.TDA(self.mf)
        self.td.nstates = nstates
        self.td.verbose = 5
        self.td.kernel()

    def analyze(self):
        return self.td.analyze()

    def absorption(self, sigma_e=0.2, wl_min=200.0, wl_max=800.0):
        wl_min = int(wl_min)
        wl_max = int(wl_max)
        n = wl_max - wl_min + 1
        wl_grid = np.linspace(wl_min, wl_max, n)

        hc = const.Planck * const.speed_of_light / (const.electron_volt * const.nano)
        e_grid = hc / wl_grid
        e_absorption = np.zeros_like(e_grid)

        excitations = self.td.e * const.physical_constants["Hartree energy in eV"][0]
        strengths = self.td.oscillator_strength()
        for excitation, strength in zip(excitations, strengths):
            e_absorption += strength * common.gaussian(e_grid, excitation, sigma_e)

        jacobian = e_absorption**2 / hc
        wl_absorption = e_absorption * jacobian

        return wl_grid, wl_absorption


class InteractiveUVVis:
    """
    An interactive UV/Vis spectrum calculation tool.
    """

    def __init__(self):
        self.atoms = None
        self.uv_vis = None

        # Output widgets and friends.
        self._xyz_input = widgets.Output()
        self._run_output = widgets.Output(layout=common.OUTPUT_LAYOUT)
        self._run_accordion = widgets.Accordion(
            [self._run_output], titles=["Programmausgabe"]
        )
        self._absorption_output = widgets.Output()
        self._absorption_accordion = widgets.Accordion(
            [self._absorption_output], titles=["Absorptionsspektrum (UV/Vis)"]
        )

        # Paste button
        self._paste_button = widgets.Button(description="Einfügen 📥")
        self._paste_button.on_click(self._on_click)

    def show(self):
        IPython.display.display(
            widgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_input,
            widgets.Label("Ausgabe", style=common.LABEL_STYLE),
            self._run_accordion,
            self._absorption_accordion,
        )

    def _run(self):
        """
        Run the calculation.
        """
        with self._run_output:
            start = time.time()
            self.uv_vis.calculate()
            end = time.time()
            minutes = (end - start) / 60
            print(f"Die Berechnung dauerte {minutes:.2f} Minuten.")

    def _show_results(self):
        """
        Show the result calculation.
        """

        with self._absorption_output:
            wl, absorption = self.uv_vis.absorption()
            plt.plot(wl, absorption)
            plt.xlabel("Wellenlänge / nm")
            plt.ylabel("Absorption / a.u.")
            plt.show()

    def _clear(self):
        self._run_output.clear_output(wait=False)
        self._absorption_output.clear_output(wait=False)

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
        if button is self._paste_button:
            self.atoms = common.paste_xyz(self._xyz_input, self._paste_button)
            if self.atoms is not None:
                self.uv_vis = UVVis(self.atoms)
                self._block()
                self._clear()
                self._run()
                self._show_results()
                self._unblock()
