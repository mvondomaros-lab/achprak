# Solution-color validation

The transmission-to-sRGB implementation passes independent numerical checks.
The INDO/S–CIS spectrum does **not** reproduce the measured spectral shape of
trans-azobenzene in ethanol well enough to validate a quantitative solution color.
Keep the preview illustrative. One compound does not justify a general correction.

## Reference and scope

Experimental data: `Data/Nägele_AB_UVvis.txt` from Eronen and Niskanen's
[Zenodo archive, version 2](https://doi.org/10.5281/zenodo.18311080).
Its README identifies the source as Nägele et al., *Femtosecond photoisomerization
of cis-azobenzene*, [Chemical Physics Letters 272, 489 (1997)](https://doi.org/10.1016/S0009-2614(97)00531-9),
included with permission from Prof. Josef Wachtveitl. The accompanying
[manuscript](https://arxiv.org/html/2505.02610v1) identifies its reference curve
as trans-azobenzene in ethanol; the older paper's title alone is not the isomer assignment.

The file covers 239.6–750.0 nm. Its README does not specify intensity units,
concentration or path length. This is a **spectral-shape comparison**, not an
absolute color or concentration validation. Original data are retained locally
in `results/color-validation/experimental-ethanol.txt`, not bundled in the app.
SHA-256: `c92ed45a3f3cd53fa92d28bad1b6efb2078b9ea8a60a2412ad233c34d7a2999f`.

Subtract the median signal at wavelengths >=650 nm (0.00504 source units), clip
negative residuals to zero, and normalize each spectrum's UV peak to 1. No fitted
wavelength shift or width is applied. For illustrative color integration only,
assume zero corrected absorption from 750 to 780 nm. These baseline and endpoint
treatments are approximations, not additional measurements.

## Calculation and results

A production `Template(configuration="trans")`, `OptMin.run()` and
`UVVis.calculate()` run converged and passed transition-output coverage. It used
seed 42, GFN1-xTB/ALPB ethanol, force threshold 0.002 eV/Å, INDO/S–CIS/MAXCI=800,
EPS=24.3, and Gaussian sigma 0.15 eV, with one BLAS/OpenMP thread. It reproduced
the existing local science benchmark.

| Feature | Experiment / nm | Calculated transition / nm | Difference / nm |
| --- | ---: | ---: | ---: |
| Strong UV band | 316.4 | 360.75 | +44.35 |
| Weak visible band | 440.4 | 498.34 | +57.94 |

The measured baseline-corrected visible/UV peak-height ratio is 0.0254.
The calculated first/second oscillator-strength ratio is 0.0000968. Equal Gaussian
widths make this also the ratio of the isolated calculated peak heights. Because
the measured bands have different shapes, this is **not** a measured oscillator-
strength ratio. The overlay nevertheless shows that visible intensity is missing.
Increasing the density factor cannot repair positions or relative band shapes.

At equal UV peak height 1, illustrative colors are sRGB (255, 255, 249) for the
experimental shape and (255, 255, 255) for the calculated shape. These are not
colors at equal physical concentrations. The native calculation gives
(255, 255, 252) even at the app's maximum density factor 10.

Changing sigma from 0.10 to 0.15 to 0.20 eV at **fixed integrated oscillator
strength** gives (255, 255, 255), (255, 255, 252), and (253, 255, 240) at factor 10.
This is sensitivity to an assumed width, not an uncertainty bound.

## Verification and reproduction

Independent NumPy integration using the original checksum-verified CIE CSVs,
rather than the bundled browser table, agrees with production JavaScript at five
density factors (0, 0.1, 1, 5, 10): identical rounded sRGB and luminance differences
below 1e-12. These numerical checks do not verify browser layout.

The offline script takes the published CIE CSVs (see [provenance](solution-color.md)),
the experimental file, and a production JSON containing `energy_ev`, `absorption`,
`excitations_ev`, `oscillator_strengths` and `coverage_complete`:

```sh
pixi run -e dev python scripts/validate_solution_color.py \
  --experimental results/color-validation/experimental-ethanol.txt \
  --spectrum results/color-validation/trans-H.json \
  --cie-xyz /tmp/achprak-cie-xyz.csv \
  --cie-d65 /tmp/achprak-cie-d65.csv \
  --output results/color-validation
```

It writes `metrics.json` (including input hashes) and `spectral-comparison.png`.
The script is opt-in; default tests gain no expensive chemistry calculations.

This one parent-trans reference does not validate cis structures, substituent
trends, absolute concentrations, mixtures, or perceptual agreement with a real
cuvette. Next steps require known-concentration spectra and a spectroscopy model
that reproduces the visible bands. Ensemble/vibronic treatment is a candidate to
investigate, not a correction established by this audit.
