import numpy as np
import pymopac

from . import common

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
            model=f"INDO CIS MAXCI=800 WRTCI=30 WRTCONF=0.2 EPS={common.SOLVENT_EPS}",
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
