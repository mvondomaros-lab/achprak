"""Offline numerical and spectral-shape validation; see docs/solution-color-validation.md."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TEST_SCALES = [0, 0.1, 1, 5, 10]


def browser_colors(spec):
    """Exercise the fixed-scale API with independently scaled test inputs."""
    requests = [
        {**spec, "absorption": [factor * value for value in spec["absorption"]]}
        for factor in TEST_SCALES
    ]
    node = """
require('./src/achprak/web/static/vendor/cie-color.js');
require('./src/achprak/web/static/solution-color.js');
const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));
console.log(JSON.stringify(input.map(spectrum => SolutionColor.estimate(spectrum))));
"""
    return json.loads(subprocess.check_output(
        ["node", "-e", node], input=json.dumps(requests).encode(), cwd=ROOT,
    ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experimental", type=Path, required=True)
    parser.add_argument("--spectrum", type=Path, required=True)
    parser.add_argument("--cie-xyz", type=Path, required=True)
    parser.add_argument("--cie-d65", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    spec = json.loads(args.spectrum.read_text())
    measured = np.loadtxt(args.experimental)
    cmf = np.loadtxt(args.cie_xyz, delimiter=",")
    daylight = np.loadtxt(args.cie_d65, delimiter=",")
    assert (
        hashlib.md5(args.cie_xyz.read_bytes()).hexdigest()
        == "17cca777db64b17170f06f67ce9d3ab7"
    )
    assert (
        hashlib.md5(args.cie_d65.read_bytes()).hexdigest()
        == "03d4eb9b837c60671627c946fb534deb"
    )
    nm = np.arange(380, 781)
    weights = np.column_stack([np.interp(nm, cmf[:, 0], cmf[:, i]) for i in (1, 2, 3)])
    light = np.interp(nm, daylight[:, 0], daylight[:, 1])
    norm = np.trapezoid(light * weights[:, 1], nm)
    matrix = np.array(
        [
            [3.2406, -1.5372, -0.4986],
            [-0.9689, 1.8758, 0.0415],
            [0.0557, -0.2040, 1.0570],
        ]
    )

    def color(absorbance):
        xyz = (
            np.trapezoid((light * 10.0 ** (-absorbance))[:, None] * weights, nm, axis=0)
            / norm
        )
        linear = np.clip(matrix @ xyz, 0, 1)
        encoded = np.where(
            linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055
        )
        return {
            "rgb": np.floor(encoded * 255 + 0.5).astype(int).tolist(),
            "luminance": float(xyz[1]),
        }

    energy = np.asarray(spec["energy_ev"])
    absorption = np.asarray(spec["absorption"])
    references = []
    for factor in TEST_SCALES:
        references.append(
            color(factor * np.interp(1239.841984 / nm, energy, absorption))
        )
    actual = browser_colors(spec)
    for a, b in zip(actual, references):
        assert a is not None, "Spectrum does not meet the browser's coverage/input checks"
        assert a["rgb"] == b["rgb"]
        assert abs(a["luminance"] - b["luminance"]) < 1e-12

    # Source file does not specify concentration/path length/intensity units.
    # Compare shapes at equal UV peak height, not absolute solution colors.
    baseline = float(np.median(measured[measured[:, 0] >= 650, 1]))
    corrected = np.maximum(0, measured[:, 1] - baseline)
    uv = (measured[:, 0] >= 270) & (measured[:, 0] <= 380)
    vis = (measured[:, 0] >= 400) & (measured[:, 0] <= 520)
    exp_uv = float(measured[uv, 0][np.argmax(corrected[uv])])
    exp_vis = float(measured[vis, 0][np.argmax(corrected[vis])])
    exp_norm = corrected / corrected[uv].max()
    exp_color = color(np.interp(nm, measured[:, 0], exp_norm, right=0))
    transitions = np.asarray(spec["excitations_ev"])
    strengths = np.asarray(spec["oscillator_strengths"])
    wavelength = np.arange(260, 781, 0.25)
    e = 1239.841984 / wavelength
    curves, sensitivity = [], []
    for sigma in [0.10, 0.15, 0.20]:
        # Preserve integrated strength while changing bandwidth.
        curve = np.sum(
            strengths[:, None]
            * (0.15 / sigma)
            * np.exp(-0.5 * ((e[None, :] - transitions[:, None]) / sigma) ** 2),
            axis=0,
        )
        curves.append(curve)
        sensitivity.append(
            {
                "sigma_ev": sigma,
                "test_input_scale_10": color(10 * np.interp(nm, wavelength, curve)),
            }
        )
    model = curves[1]
    model_uv = (wavelength >= 270) & (wavelength <= 380)
    model_norm = model / model[model_uv].max()
    report = {
        "scope": "One trans-H ethanol spectrum; shape comparison only, no absolute color validation",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "implementation_sha256": {
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in [
                "scripts/validate_solution_color.py",
                "src/achprak/web/static/solution-color.js",
                "src/achprak/web/static/vendor/cie-color.js",
            ]
        },
        "input_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [args.experimental, args.spectrum]
        },
        "independent_numerical_checks": {
            "cases": len(actual),
            "test_input_scales": TEST_SCALES,
            "rgb_exact_match": True,
            "luminance_tolerance": 1e-12,
        },
        "experimental_range_nm": [float(measured[0, 0]), float(measured[-1, 0])],
        "experimental_baseline_subtracted": baseline,
        "experimental_peaks_nm": [exp_vis, exp_uv],
        "calculated_first_transitions_nm": (1239.841984 / transitions[:2]).tolist(),
        "experimental_visible_to_uv_peak_ratio": float(
            corrected[vis].max() / corrected[uv].max()
        ),
        "calculated_isolated_first_to_second_strength_ratio": float(
            strengths[0] / strengths[1]
        ),
        "shape_only_color_at_uv_peak_1": {
            "experimental": exp_color,
            "calculated": color(np.interp(nm, wavelength, model_norm)),
        },
        "bandwidth_sensitivity_fixed_integrated_strength": sensitivity,
        "fixed_scale_app_result": actual[TEST_SCALES.index(1)],
        "scaled_input_test_results": actual,
    }
    (args.output / "metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    from achprak.plot_style import STYLE, PRIMARY, ACCENT, style_axes

    with plt.rc_context(STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
        for ax in axes:
            ax.plot(
                measured[:, 0],
                exp_norm,
                label="Measured, ethanol",
                color=ACCENT,
                linestyle="--",
            )
            ax.plot(wavelength, model_norm, label="INDO/S–CIS", color=PRIMARY)
            ax.set_xlabel("Wavelength / nm")
            ax.set_ylabel("Relative absorption (UV peak = 1)")
            style_axes(ax, german=False)
        axes[0].set(xlim=(270, 550), ylim=(0, 1.1), title="trans-H: spectral shape")
        axes[0].legend()
        axes[1].set(xlim=(400, 550), ylim=(0, 0.04), title="Visible band: enlarged")
        fig.savefig(args.output / "spectral-comparison.png", dpi=180)
        plt.close(fig)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
