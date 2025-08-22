import IPython.display
import ipywidgets
import matplotlib.pyplot as plt
import numpy as np
import pymopac
import scipy.constants as const

from . import common

MAX_MEMORY = 8000

EMIN = 1.5
EMAX = 5.5
SIGMA = 0.3


def parse_mopac_excitations(fname):
    in_block = False
    lines = []

    with open(fname) as f:
        for line in f:
            line = line.strip()
            if line.strip().startswith(
                "CI trans.  energy frequency wavelength oscillator-"
            ):
                in_block = True
                for _ in range(3):
                    line = next(f)
            if in_block:
                if len(line) == 0:
                    break
                lines.append(line.split())
    excitations = np.array([item[1] for item in lines], dtype=np.float64)
    strengths = np.array([item[4] for item in lines], dtype=np.float64)
    return excitations, strengths


class UVVis:
    """
    Compute a UV-Vis spectrum.
    """

    def __init__(self, atoms):
        self.atoms = atoms
        xyz = common.atoms_to_xyz(atoms)
        self.mopac = pymopac.MopacInput(
            xyz,
            model=f"INDO CIS EPS={common.SOLVENT_EPS}",
            addHs=False,
            preopt=False,
            aux=False,
            stream=True,
        )
        self.excitations = None
        self.oscillator_strengths = None

    def calculate(self):
        self.mopac.run()
        self.excitations, self.oscillator_strengths = parse_mopac_excitations(
            self.mopac.outpath
        )

    def spectrum(self):
        energy = np.linspace(EMIN, EMAX, 1000)
        spectrum = np.zeros_like(energy)

        for e, f in zip(self.excitations, self.oscillator_strengths):
            spectrum += f * common.gaussian(x=energy, mu=e, sigma=SIGMA)

        # Normalize, so that isolated peaks have the same height as the oscillator strength.
        spectrum *= np.sqrt(2.0 * np.pi) * SIGMA

        return energy, spectrum

    def plot(self, ax):
        """
        Plot the UV-Vis spectrum.
        """
        energy, spectrum = self.spectrum()

        ax.plot(energy, spectrum, color="C0")

        for e, f in zip(self.excitations, self.oscillator_strengths):
            if EMIN < e < EMAX:
                ax.plot([e, e], [0, f], color="C1")
                if f > 0.15:
                    ax.text(
                        e,
                        1.05 * f,
                        f"{e:.3g}",
                        color="black",
                        ha="center",
                        va="bottom",
                        rotation=45,
                    )

        ax.set_xlim(EMIN, EMAX)
        ax.set_ylim(0.0, 1.15 * np.max(spectrum))
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
        self._xyz_init_output = ipywidgets.Output()
        self._run_output = ipywidgets.Output(layout=common.OUTPUT_LAYOUT)
        self._run_accordion = ipywidgets.Accordion(
            [self._run_output], titles=["Programmausgabe"]
        )
        self._absorption_output = ipywidgets.Output()
        self._absorption_accordion = ipywidgets.Accordion(
            [self._absorption_output], titles=["Absorptionsspektrum (UV/Vis)"]
        )

        # Paste button
        self._paste_button = ipywidgets.Button(description=common.PASTE_TEXT)
        self._paste_button.on_click(self._on_click)

        # Run Button
        self._run_button = ipywidgets.Button(
            description=common.RUN_START_TEXT, disabled=True
        )
        self._run_button.on_click(self._on_click)

    def show(self):
        IPython.display.display(
            ipywidgets.Label("Koordinaten (XYZ-Format)", style=common.LABEL_STYLE),
            self._paste_button,
            self._xyz_init_output,
            ipywidgets.Label("Berechnung", style=common.LABEL_STYLE),
            self._run_button,
            self._run_accordion,
            self._absorption_accordion,
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
            self._run_button.description = common.RUN_OK_TEXT
            self._update()

    def _reset(self):
        """
        Reset the tool.
        """
        self._xyz_init_output.clear_output()
        self._run_output.clear_output()
        self._absorption_output.clear_output()
        self.atoms = None
        self.uv_vis = None

        self._run_button.disabled = True
        self._run_button.description = common.RUN_START_TEXT

    def _run(self):
        """
        Run the calculation.
        """
        with self._run_output:
            self.uv_vis = UVVis(self.atoms)
            self.uv_vis.calculate()

    def _update(self):
        with self._absorption_output:
            fig, ax = plt.subplots()
            self.uv_vis.plot(ax)
            plt.show()
