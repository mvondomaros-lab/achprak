# Experimental comparison of spectrum and color

This is a recorded spectral-shape study, first committed as `8021fe5` on
2026-09-16. That revision documents the earlier adjustable-density interface;
the exact calculation date and source revision were not recorded separately.
The numerical results below are retained, not presented as a fresh run of the
current application. See [the current model](solution-color.md) for the fixed
absorbance scale and weighted light transmission.

In the recorded study, the transmission-to-sRGB implementation passed independent numerical checks. The
INDO/S–CIS spectrum does **not** reproduce the measured spectral shape of
trans-azobenzene in ethanol well enough to validate a quantitative solution color.
Keep the preview illustrative. One compound does not justify a general correction.

Two separate checks are reported here: whether the software converts a spectrum to
display color correctly, and whether the calculated spectrum resembles an
experimental spectrum. The first passes; the second reveals substantial errors.
See the [color model](solution-color.md) for the fixed absorbance scale,
standard daylight (D65), the CIE color-response tables and the sRGB display space.
Wavelengths below are in nanometres (nm), and photon energies in electronvolts
(eV).

## Reference and scope

Experimental data: `Data/Nägele_AB_UVvis.txt` from Eronen and Niskanen's [Zenodo
archive, version 2](https://doi.org/10.5281/zenodo.18311080). Its README
identifies the source as Nägele et al., *Femtosecond photoisomerization of
cis-azobenzene*, [Chemical Physics Letters 272, 489
(1997)](https://doi.org/10.1016/S0009-2614(97)00531-9), included with permission
from Prof. Josef Wachtveitl. The accompanying
[manuscript](https://arxiv.org/html/2505.02610v1) identifies its reference curve
as trans-azobenzene in ethanol; the older paper's title alone is not the isomer
assignment.

The file covers 239.6–750.0 nm. Its README does not specify intensity units,
concentration or path length. This is a **spectral-shape comparison**, not an
absolute color or concentration validation. Original data are retained locally in
`results/color-validation/experimental-ethanol.txt`, not bundled in the app.
SHA-256 checksum (for identifying the exact input file):
`c92ed45a3f3cd53fa92d28bad1b6efb2078b9ea8a60a2412ad233c34d7a2999f`.

Subtract the median signal at wavelengths >=650 nm (0.00504 source units), clip
negative residuals to zero, and normalize each spectrum's UV peak to 1. No fitted
wavelength shift or width is applied. For illustrative color integration only,
assume zero corrected absorption from 750 to 780 nm. These baseline and endpoint
treatments are approximations, not additional measurements.

## Calculation and results

The normal application workflow generated an unsubstituted trans starting
structure, optimized a minimum and calculated a spectrum. The structure converged,
and the printed transitions covered the required spectral range. It used seed 42,
GFN1-xTB/ALPB ethanol, force threshold 0.002 eV/Å, INDO/S–CIS/MAXCI=800, COSMO
dielectric constant EPS=24.3, and Gaussian standard deviation sigma = 0.15 eV,
with one numerical-library compute thread. The [method
overview](science-decisions.md) explains these settings.

Differences are calculated minus experimental wavelengths. Positive values
therefore indicate a shift toward longer wavelengths. Calculated entries are
discrete transitions; experimental entries are band maxima.

| Feature | Experiment / nm | Calculated transition / nm | Difference / nm |
| --- | ---: | ---: | ---: |
| Strong UV band | 316.4 | 360.75 | +44.35 |
| Weak visible band | 440.4 | 498.34 | +57.94 |

The measured baseline-corrected visible/UV peak-height ratio is 0.0254. The
calculated first/second oscillator-strength ratio (dimensionless transition
intensities) is 0.0000968. Equal Gaussian widths make this also the ratio of the
isolated calculated peak heights. Because the measured bands have different
shapes, this is **not** a measured oscillator-strength ratio. The comparison
nevertheless shows that visible absorption is strongly underestimated relative to
the ultraviolet band. Increasing the density factor cannot repair positions or
relative band shapes.

At equal UV peak height 1, illustrative colors are sRGB (255, 255, 249) for the
experimental shape and (255, 255, 255) for the calculated shape. These are not
colors at equal physical concentrations. The native calculation gave (255, 255,
252) at the former slider's maximum factor 10; that factor is not the current app setting.

Changing sigma from 0.10 to 0.15 to 0.20 eV at **fixed integrated oscillator
strength** gives (255, 255, 255), (255, 255, 252), and (253, 255, 240) at factor
10. This is sensitivity to an assumed width, not an uncertainty bound.

## Repeating the comparison with the current implementation

On 2026-09-23, the corrected validator was run with the retained calculated
spectrum and the original checksum-verified CIE files. All five scaled-input
checks passed: rounded sRGB matched exactly and luminance differences were below
10⁻¹². At the app's fixed scale, the retained spectrum gives sRGB (255, 255, 255)
and weighted light transmission of approximately 99.991%. No chemistry calculation
was rerun. The tested browser implementation has SHA-256
`8a3bd4e128190fd3aa511357b1e116821d485bb271774af4ba292d616a2c7192`;
the retained spectrum has SHA-256
`fcb3da09e1a252e15901097299de744dd859d0095e82aa473c2afd86feeae530`.

The command below assumes the experimental data, CIE tables and calculated
spectrum have already been obtained. It does not download the reference files or
run the electronic-structure calculation. Paths in the example are local input
locations; adapt them to where those files are stored.

The validator compares independent NumPy integration of the original
checksum-verified CIE CSVs with production JavaScript. It scales copies of the
input absorption curve by 0, 0.1, 1, 5, and 10 and calls the fixed-scale browser
API for each. These are numerical test inputs, not available UI settings.
Acceptance requires identical rounded sRGB and luminance differences below
10⁻¹². Only the unscaled input represents the current app prediction.

The script, run separately from the web application, takes the published CIE CSVs
(see [provenance](solution-color.md)), the experimental file, and an application
spectrum saved as a JSON data file containing `energy_ev`, `absorption`,
`excitations_ev`, `oscillator_strengths` and `coverage_complete`.

To obtain that JSON, calculate the required spectrum in the app, then open
`api/session` relative to the app's base URL in the same browser session (locally,
`http://127.0.0.1:8000/api/session`). In the `molecules` array, identify the required
structure and save its complete `spectrum` object as `trans-H.json`, not the
enclosing session response. Under JupyterHub, retain the app's proxy prefix.
Image export does not contain these numerical data.

Download the original CIE CSV files from the [documented source](solution-color.md#data-provenance)
and extract the experimental file from the versioned archive above. Node.js is
required for the production-JavaScript comparison.

```sh
pixi run -e dev python scripts/validate_solution_color.py \
  --experimental results/color-validation/experimental-ethanol.txt \
  --spectrum results/color-validation/trans-H.json \
  --cie-xyz /tmp/achprak-cie-xyz.csv \
  --cie-d65 /tmp/achprak-cie-d65.csv \
  --output results/color-validation
```

It writes `metrics.json` (including input and implementation hashes and a UTC
timestamp) and `spectral-comparison.png`. The report distinguishes the fixed-scale
app result from scaled-input tests and bandwidth sensitivity at test scale 10.
Run the script explicitly when reproducing this comparison; it is not part of the
default test suite.

This one parent-trans reference does not validate cis structures, substituent
trends, absolute concentrations, mixtures, or perceptual agreement with a real
cuvette. Next steps require known-concentration spectra and a spectroscopy model
that reproduces the visible bands. Averaging over conformers and accounting for
coupling between electronic and vibrational transitions are possible
investigations, not corrections established by this comparison.
