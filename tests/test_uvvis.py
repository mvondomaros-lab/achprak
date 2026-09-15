"""Spectral output coverage, independently of the expensive MOPAC calculation."""

import numpy as np
import pytest
from ase import Atoms

from achprak import uvvis


@pytest.mark.parametrize(
    "first,second,expected_runs,complete",
    [
        (np.linspace(2, 7, 99), None, 1, True),
        (np.linspace(2, 5, 99), np.linspace(2, 8, 300), 2, True),
        (np.linspace(2, 5, 99), np.linspace(2, 6, 300), 2, False),
        (np.linspace(2, 5, 40), None, 1, False),
    ],
)
def test_output_coverage(monkeypatch, first, second, expected_runs, complete):
    jobs = []

    class Mopac:
        def __init__(self, xyz, **kwargs):
            self.model = kwargs["model"]
            self.outpath = len(jobs)
            self.runs = 0
            jobs.append(self)

        def run(self):
            self.runs += 1

    def parse(index):
        energies = first if index == 0 else second
        return energies, np.ones(len(energies))

    monkeypatch.setattr(uvvis.pymopac, "MopacInput", Mopac)
    monkeypatch.setattr(uvvis, "parse_mopac_excitations", parse)
    spec = uvvis.UVVis(Atoms("H", positions=[[0, 0, 0]]))
    spec.calculate()
    assert sum(job.runs for job in jobs) == expected_runs
    assert spec.coverage_complete is complete
    assert all("MAXCI=800" in job.model for job in jobs)
    if expected_runs == 2:
        assert "WRTCI=800" in jobs[-1].model


def test_parse_realistic_transition_table(tmp_path):
    output = tmp_path / "spectrum.out"
    output.write_text(
        "CI trans.  energy frequency wavelength oscillator-\n"
        "             (eV)   (cm-1)     (nm)     strength\n\n"
        "1 2.50 20163.9 495.9 0.001\n"
        "2 3.50 28229.5 354.2 0.750\n\n"
    )
    energies, strengths = uvvis.parse_mopac_excitations(output)
    np.testing.assert_allclose(energies, [2.5, 3.5])
    np.testing.assert_allclose(strengths, [0.001, 0.75])
