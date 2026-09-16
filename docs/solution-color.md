# Approximate solution color

The spectrum panel estimates transmitted color from the existing INDO/S–CIS
broadened spectrum. This is an illustrative prediction, not an experimentally
validated solution color or a concentration measurement. No new chemistry
calculation is required. The control persists while switching structures so
spectra can be compared at the same relative scale.

## Interpreting the preview

The color patch represents light transmitted through the selected structure's
calculated absorption spectrum. Increasing the slider increases the assumed
absorbance and therefore reduces transmitted light. Keep the same slider value
when comparing structures. The value is a relative scale, not a concentration; the
model does not supply calibrated molar absorption coefficients.

The conversion uses **D65**, a standard daylight spectrum, and the **CIE 1931
2-degree standard observer**, a tabulated model of human color response. **sRGB**
is the display color space used for the resulting red, green and blue values.
These choices define a reproducible display calculation, not the appearance of a
particular sample under every lamp or on every monitor.

<details>
<summary>Equations and numerical integration</summary>

In the following expressions, lambda is wavelength in nanometres (nm), E is photon
energy in electronvolts (eV), h is Planck's constant and c is the speed of light.
I is the application's relative spectral intensity, A is dimensionless absorbance,
and T is the fraction of incident light transmitted.

- Interpolate the existing energy-domain curve at E = hc/lambda, using
  hc = 1239.841984 eV nm. No intensity rescaling is applied when changing the horizontal axis from energy
  to wavelength: absorbance is a response at a wavelength, not a probability
  density that must be redistributed between bins.
- Set dimensionless absorbance A(lambda) = s I(lambda), with slider s in [0, 10].
  Keep the original relative intensities; do not normalize individual spectra.
  A path length of 1 cm is assumed for interpretation, but neither path length
  nor concentration is independently calibrated by s.
- Apply T(lambda) = 10^(-A(lambda)). Integrate T times D65 times the CIE 1931
  2-degree color-matching functions by the trapezoidal rule at 1 nm intervals,
  over 380–780 nm. The very small observer tails outside this range are omitted.
- Normalize CIE XYZ (three integrated color-response values) by the unattenuated illuminant's Y integral. Convert D65 XYZ to
  sRGB, clip linear channels to [0, 1], then apply the nonlinear sRGB display
  encoding. Clipping limits colors to the displayable range.
  Preserve luminance; do not brighten each swatch independently.
- Suppress the swatch if the spectrum reports incomplete transition coverage,
  does not cover the visible interval, or contains invalid samples. The existing
  coverage flag is an output check, not proof of configuration convergence.

</details>

## Assumptions and omissions

The view represents the selected structure alone, without isomer mixtures,
conformer averaging, aggregation, scattering or fluorescence. It assumes a white
surround and standard daylight. Experimental band positions, intensities and
widths can differ, and screen viewing conditions affect perceived appearance.

## Data provenance

[`cie-color.js`](../src/achprak/web/static/vendor/cie-color.js) contains a joined,
cropped adaptation of:

- CIE (2019), *Colour-matching functions of CIE 1931 standard colorimetric
  observer*, International Commission on Illumination, Vienna, AT.
  <https://doi.org/10.25039/CIE.DS.xvudnb9b>
  Original comma-separated data file (CSV), MD5 checksum: `17cca777db64b17170f06f67ce9d3ab7`.
- CIE (2019), *CIE standard illuminant D65*, same publisher.
  <https://doi.org/10.25039/CIE.DS.hjfjmt59>
  Original comma-separated data file (CSV), MD5 checksum: `03d4eb9b837c60671627c946fb534deb`.

The adapted data file is CC BY-SA 4.0:
<https://creativecommons.org/licenses/by-sa/4.0/>. Source CSVs are available at
`https://files.cie.co.at/Publications-datasets/` using filenames
`CIE_xyz_1931_2deg.csv` and `CIE_std_illum_D65.csv`. Join on wavelength and retain
380 through 780 nm inclusive; retain all published precision. Source checksums
were verified when generating the bundled table. No runtime network dependency.

## Validation before quantitative claims

An [initial experimental comparison](solution-color-validation.md) found large
band-position errors and strongly underestimated visible-band intensity for
trans-azobenzene in ethanol. Numerical color integration passes, but quantitative
solution-color prediction is not validated. No measured spectra are bundled.
Collect full molar absorption spectra in ethanol with known path length,
concentration, temperature and isomer composition, starting with the parent,
para-OMe, para-NMe2 and selected donor–acceptor derivatives. Compare visible band
positions, integrated intensities and widths before fitting corrections. Reserve
some derivatives for validation rather than fitting all available measurements.
Measured spectra can use the same transmission/color integration with A(lambda) =
epsilon(lambda) c l, where epsilon is the molar absorption coefficient, c the
concentration and l the optical path length, in consistent units. Here c denotes
concentration, rather than the speed of light used above. Do not infer physical
concentrations from the current slider.

Numerical checks: `node --test tests/test_solution_color.cjs`.
