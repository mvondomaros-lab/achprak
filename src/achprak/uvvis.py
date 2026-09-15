import sys
from contextlib import redirect_stdout

import numpy as np
import pymopac

from . import common

EMIN = 1.5
EMAX = 5.5
SIGMA = 0.15
MAXCI = 800
PRINTED_STATES = 100
# At four standard deviations, an individual Gaussian is below 0.04% of its peak.
COVERAGE_MARGIN = 4 * SIGMA


class MopacProgressStream:
    """Forward output unchanged and recognize completed, ordered INDO milestones."""

    def __init__(self, output, observer):
        self.output = output
        self.observer = observer
        self.pending = ""
        self.stage = 0

    def write(self, text):
        self.output.write(text)
        self.pending += text
        while "\n" in self.pending:
            line, self.pending = self.pending.split("\n", 1)
            line = line.strip()
            stage = 0
            if line.startswith("RHF CALCULATION,"):
                stage = 1
            elif line == "MOLECULAR ORBITALS":
                stage = 2
            elif line.startswith("CI excitations="):
                stage = 3
            elif line.startswith("CI trans.  energy frequency wavelength oscillator-"):
                stage = 4
            if stage > self.stage:
                self.stage = stage
                phases = ("", "electrons", "configurations", "excited_states", "transitions")
                self.observer(phases[stage])
        return len(text)

    def flush(self):
        self.output.flush()


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

    def __init__(self, atoms, maxci=MAXCI):
        self.atoms = atoms
        self.maxci = maxci
        self.mopac = self._input(min(PRINTED_STATES, maxci))
        self.excitations = None
        self.oscillator_strengths = None
        self.coverage_complete = False

    def _input(self, printed_states):
        return pymopac.MopacInput(
            common.atoms_to_xyz(self.atoms),
            model=f"INDO CIS MAXCI={self.maxci} WRTCI={printed_states} WRTCONF=0.2 EPS={common.SOLVENT_EPS}",
            addHs=False,
            preopt=False,
            aux=False,
            stream=True,
        )

    def _run(self, observer):
        if observer is None:
            self.mopac.run()
        else:
            with redirect_stdout(MopacProgressStream(sys.stdout, observer)):
                self.mopac.run()

    def calculate(self, observer=None):
        self._run(observer)
        if observer:
            observer("read_transitions")
        self.excitations, self.oscillator_strengths = parse_mopac_excitations(
            self.mopac.outpath
        )
        # WRTCI only controls output. Request all available states if the first
        # output block does not cover the plot plus the broadening margin.
        if (
            self.maxci > PRINTED_STATES
            # MOPAC counts the ground state in WRTCI: 100 gives 99 transitions.
            and len(self.excitations) >= PRINTED_STATES - 1
            and self.excitations.max() < EMAX + COVERAGE_MARGIN
        ):
            self.mopac = self._input(self.maxci)
            if observer:
                observer("expanded_output")
            # Keep the reason for the repeated run visible throughout it.
            self._run(None)
            if observer:
                observer("read_transitions")
            self.excitations, self.oscillator_strengths = parse_mopac_excitations(
                self.mopac.outpath
            )
        self.coverage_complete = bool(
            len(self.excitations) and self.excitations.max() >= EMAX + COVERAGE_MARGIN
        )

    def spectrum(self):
        energy = np.linspace(EMIN, EMAX, 1000)
        spectrum = np.zeros_like(energy)

        for e, f in zip(self.excitations, self.oscillator_strengths):
            spectrum += f * common.gaussian(x=energy, mu=e, sigma=SIGMA)

        # Normalize, so that isolated peaks have the same height as the oscillator strength.
        spectrum *= np.sqrt(2.0 * np.pi) * SIGMA

        return energy, spectrum
