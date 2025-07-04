import time

from . import common

import numpy as np
import pyscf.dft
import pyscf.tddft

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

    def calculate(self, basis="6-31G(d)", xc="B3LYP", nstates=5):
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

    def absorption_spectrum(self, start, stop, sigma):
        energy = np.linspace(start, stop, 1000)
        absorption = np.zeros_like(energy)

        excitations = self.td.e * const.physical_constants["Hartree energy in eV"][0]
        strengths = self.td.oscillator_strength()
        for excitation, strength in zip(excitations, strengths):
            absorption += strength * common.gaussian(
                x=energy, mu=excitation, sigma=sigma
            )

        return energy, absorption


class UVVisTool:
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
        Show the result of the calculation.
        """

        with self._absorption_output:
            start = 1.5
            stop = 5.5
            sigma = 0.1
            energy, absorption = self.uv_vis.absorption_spectrum(start, stop, sigma)
            absorption *= np.sqrt(2.0 * np.pi) * sigma

            hc = (
                const.Planck * const.speed_of_light / (const.electron_volt * const.nano)
            )
            wl_start = int(hc / start / 100.0) * 100
            wl_stop = int(hc / stop / 100.0) * 100
            wl_ticks = np.linspace(wl_start, wl_stop, 9, dtype=np.int64)
            wl_tick_positions = hc / wl_ticks

            fig, ax1 = plt.subplots()

            ax1.plot(energy, absorption, color="C0")
            excitations = (
                self.uv_vis.td.e * const.physical_constants["Hartree energy in eV"][0]
            )
            strengths = self.uv_vis.td.oscillator_strength()

            for e, f in zip(excitations, strengths):
                ax1.plot([e, e], [0, f], color="C1")
                if f > 0.1 and start < e < stop:
                    ax1.text(
                        e + 0.5 * sigma,
                        f + 0.02,
                        f"{e:.2g} eV",
                        color="C1",
                        ha="center",
                        va="bottom",
                    )

            ax1.set_xlim(start - 0.5 * sigma, stop + 0.5 * sigma)
            ax1.set_ylim(0.0, 1.1 * np.max(absorption))

            ax1.set_xlabel("Energie / eV")
            ax1.set_ylabel("Absorption / a.u.")

            ax2 = plt.twiny()
            ax2.set_xlim(start - 0.5 * sigma, stop + 0.5 * sigma)
            ax2.set_xticks(wl_tick_positions, wl_ticks, rotation=50)
            ax2.grid(False)
            ax2.set_xlabel("Wellenlänge / nm")

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
