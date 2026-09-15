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


def test_mopac_progress_handles_split_lines_and_ignores_keyword_echoes():
    from io import StringIO

    output = StringIO()
    phases = []
    stream = uvvis.MopacProgressStream(output, phases.append)
    chunks = [
        " * CIS - C.I. USES 1 ELECTRON EXCITATIONS ONLY\n",
        "RHF CALC", "ULATION, NO. OF DOUBLY OCCUPIED LEVELS = 48\n",
        "MOLECULAR ORBITALS\nROOT NO. 1 2 3\n",
        "CI excitations= 800: =800\n",
        "CI excitations= 800: =800\n",
        "CI trans.  energy frequency wavelength oscillator---------\n",
        "MOLECULAR ORBITALS\n",  # Do not regress within one run.
    ]
    for chunk in chunks:
        assert stream.write(chunk) == len(chunk)
    stream.flush()
    assert output.getvalue() == "".join(chunks)
    assert phases == ["electrons", "configurations", "excited_states", "transitions"]


def test_progress_reports_expanded_output_and_restores_stdout(monkeypatch):
    import sys

    jobs = []

    class Mopac:
        def __init__(self, *args, **kwargs):
            self.outpath = len(jobs)
            jobs.append(self)

        def run(self):
            print("RHF CALCULATION, NO. OF DOUBLY OCCUPIED LEVELS = 48")
            print("CI excitations= 800: =800")

    monkeypatch.setattr(uvvis.pymopac, "MopacInput", Mopac)
    monkeypatch.setattr(uvvis, "parse_mopac_excitations", lambda index: (
        np.linspace(2, 5 if index == 0 else 8, 99), np.ones(99),
    ))
    original = sys.stdout
    phases = []
    spec = uvvis.UVVis(Atoms("H", positions=[[0, 0, 0]]))
    spec.calculate(observer=phases.append)
    assert sys.stdout is original
    assert phases == ["electrons", "excited_states", "read_transitions",
                      "expanded_output", "read_transitions"]
    assert spec.coverage_complete


def test_progress_restores_stdout_on_mopac_failure(monkeypatch):
    import sys
    from types import SimpleNamespace

    def fail():
        raise RuntimeError("MOPAC failed")

    monkeypatch.setattr(uvvis.pymopac, "MopacInput", lambda *args, **kwargs: SimpleNamespace(run=fail))
    spec = uvvis.UVVis(Atoms("H", positions=[[0, 0, 0]]))
    original = sys.stdout
    with pytest.raises(RuntimeError, match="MOPAC failed"):
        spec.calculate(observer=lambda phase: None)
    assert sys.stdout is original
