import time

from . import common

import numpy as np
import pyscf.dft
import pyscf.tddft

import ipywidgets as widgets
import IPython.display
import matplotlib.pyplot as plt
import scipy.constants as const

EMIN = 1.5
EMAX = 5.5
SIGMA = 0.2


class UVVis:
    """
    Compute a UV-Vis spectrum.
    """

    def __init__(self, atoms):
        self.mol = common.atoms_to_pyscf(atoms)

        self.energy = None
        self.mf = None
        self.td = None

    def calculate(self, basis="STO-3G", xc="LDA", nstates=5):
        self.mol.basis = basis
        self.mol = self.mol.build()

        self.mf = pyscf.dft.RKS(self.mol).density_fit().PCM()
        self.mf.with_solvent.method = "IEF-PCM"
        self.mf.with_solvent.eps = common.SOLVENT_EPS
        self.mf.xc = xc
        self.mf.verbose = 4
        self.mf.kernel()

        self.td = pyscf.tddft.TDA(self.mf)
        self.td.nstates = nstates
        self.td.verbose = 5
        self.td.kernel()

    def excitations(self):
        excitations = self.td.e * const.physical_constants["Hartree energy in eV"][0]
        strengths = self.td.oscillator_strength()
        return excitations, strengths

    def spectrum(self):
        energy = np.linspace(EMIN, EMAX, 1000)
        spectrum = np.zeros_like(energy)
        excitations, strengths = self.excitations()

        for e, s in zip(excitations, strengths):
            spectrum += s * common.gaussian(x=energy, mu=e, sigma=SIGMA)

        # Normalize, so that the peaks are as high as the oscillator strengths.
        spectrum *= np.sqrt(2.0 * np.pi) * SIGMA

        return energy, spectrum

    def plot(self, ax):
        """
        Plot the UV-Vis spectrum.
        """
        excitations, strengths = self.excitations()
        energy, spectrum = self.spectrum()

        ax.plot(energy, spectrum, color="C0")

        for e, s in zip(excitations, strengths):
            if EMIN < e < EMAX:
                ax.plot([e, e], [0, s], color="black")
                if s > 0.1:
                    ax.text(
                        e + 0.1,
                        s + 0.02,
                        f"{e:.2g} eV",
                        color="C1",
                        ha="center",
                        va="bottom",
                    )

        ax.set_xlim(EMIN, EMAX)
        ax.set_ylim(0.0, 1.1 * np.max(spectrum))
        ax.set_xlabel("Energie / eV")
        ax.set_ylabel("Absorption / a.u.")

        axw = plt.twiny()
        hc = const.Planck * const.speed_of_light / (const.electron_volt * const.nano)
        wmin = np.round(hc / EMIN, decimals=-2)
        wmax = np.round(hc / EMAX, decimals=-2)
        wticks = np.linspace(wmin, wmax, 9, dtype=np.int64)
        axw.set_xlim(EMIN, EMAX)
        axw.set_xticks(hc / wticks, wticks, rotation=45)
        axw.grid(False)
        axw.set_xlabel("Wellenlänge / nm")


class UVVisTool:
    """
    An interactive UV/Vis spectrum calculation tool.
    """

    def __init__(self):
        self.atoms = None
        self.uv_vis = None

        # Output widgets and friends.
        self._xyz_init_output = widgets.Output()
        self._run_output = widgets.Output(layout=common.OUTPUT_LAYOUT)
        self._run_accordion = widgets.Accordion(
            [self._run_output], titles=["Programmausgabe"]
        )
        self._absorption_output = widgets.Output()
        self._absorption_accordion = widgets.Accordion(
            [self._absorption_output], titles=["Absorptionsspektrum (UV/Vis)"]
        )

        # Paste button
        self._paste_button = widgets.Button(description=common.PASTE_TEXT)
        self._paste_button.on_click(self._on_click)

    def show(self):
        IPython.display.display(
            widgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_init_output,
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
            print(f"Wall time: {minutes:.2f} minutes")

    def _show_results(self):
        """
        Show the result of the calculation.
        """

        with self._absorption_output:
            fig, ax = plt.subplots()
            self.uv_vis.plot(ax)
            plt.show()

    def _clear(self):
        self._run_output.clear_output(wait=False)
        self._absorption_output.clear_output(wait=False)

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
        if button is self._paste_button:
            self.atoms = common.clipboard_to_atoms(
                button=button, output=self._xyz_init_output
            )

            if self.atoms is not None:
                self.uv_vis = UVVis(self.atoms)
                self._block()
                self._clear()
                self._run()
                self._show_results()
                self._unblock()
