# Approximate solution color

The spectrum panel estimates transmitted color from the existing INDO/S–CIS
broadened spectrum. This is an illustrative prediction, not an experimentally
validated solution color or a concentration measurement. No new chemistry
calculation is required. The control persists while switching structures so
spectra can be compared at the same relative scale.

## Calculation

- Interpolate the existing energy-domain curve at E = hc/lambda, using
  hc = 1239.841984 eV nm. Do not apply a density Jacobian: absorbance is a
  wavelength-dependent response, not a probability density.
- Set dimensionless absorbance A(lambda) = s I(lambda), with slider s in [0, 10].
  Keep the original relative intensities; do not normalize individual spectra.
  The assumed path length is 1 cm, but s has no calibrated concentration meaning.
- Apply T(lambda) = 10^(-A(lambda)). Integrate T times D65 times the CIE 1931
  2-degree color-matching functions by the trapezoidal rule at 1 nm intervals,
  over 380–780 nm. The very small observer tails outside this range are omitted.
- Normalize XYZ by the unattenuated illuminant's Y integral. Convert D65 XYZ to
  sRGB, clip linear channels to [0, 1], then apply the sRGB transfer function.
  Preserve luminance; do not brighten each swatch independently.
- Suppress the swatch if the spectrum reports incomplete transition coverage,
  does not cover the visible interval, or contains invalid samples. The existing
  coverage flag is an output check, not proof of configuration convergence.

The view represents the selected structure alone, without isomer mixtures,
conformer averaging, aggregation, scattering or fluorescence. It assumes a white
surround and standard daylight. Experimental band positions, intensities and
widths can differ, and screen viewing conditions affect perceived appearance.

## Data provenance

`static/vendor/cie-color.js` contains a joined, cropped adaptation of:

- CIE (2019), *Colour-matching functions of CIE 1931 standard colorimetric
  observer*, International Commission on Illumination, Vienna, AT.
  <https://doi.org/10.25039/CIE.DS.xvudnb9b>
  Original CSV MD5: `17cca777db64b17170f06f67ce9d3ab7`.
- CIE (2019), *CIE standard illuminant D65*, same publisher.
  <https://doi.org/10.25039/CIE.DS.hjfjmt59>
  Original CSV MD5: `03d4eb9b837c60671627c946fb534deb`.

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
Measured spectra can use the same transmission/color integration after replacing
the relative absorbance with epsilon(lambda) c l. Do not infer physical
concentrations from the current slider.

Numerical checks: `node --test tests/test_solution_color.cjs`.
