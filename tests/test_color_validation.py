"""Regression for the offline validator's fixed-scale browser API integration."""

import importlib.util
from pathlib import Path
import shutil

import numpy as np
import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is optional")
def test_validator_scales_inputs_and_preserves_original():
    source = Path(__file__).resolve().parents[1] / "scripts/validate_solution_color.py"
    spec = importlib.util.spec_from_file_location("color_validation", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    spectrum = {
        "energy_ev": [1.5, 5.5],
        "absorption": [1.0, 1.0],
        "coverage_complete": True,
    }
    results = module.browser_colors(spectrum)
    # A flat absorbance has an analytical transmission, independent of observer data.
    np.testing.assert_allclose(
        [result["luminance"] for result in results],
        10.0 ** -np.asarray(module.TEST_SCALES), rtol=1e-12, atol=1e-15,
    )
    assert results[0]["rgb"] == [255, 255, 255]
    assert results[-1]["rgb"] == [0, 0, 0]
    assert spectrum["absorption"] == [1.0, 1.0]
