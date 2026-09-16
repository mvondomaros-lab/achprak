/* Approximate transmitted color; physical concentration is not inferred. */
(() => {
  const HC = 1239.841984;
  const encode = (v) => v <= 0.0031308 ? 12.92 * v : 1.055 * v ** (1 / 2.4) - 0.055;

  function estimate(spectrum, density = 1) {
    const energy = spectrum?.energy_ev, absorption = spectrum?.absorption;
    if (spectrum?.coverage_complete === false) return null;
    if (!Array.isArray(energy) || !Array.isArray(absorption) || energy.length < 2 ||
        energy.length !== absorption.length || !Number.isFinite(density) || density < 0 ||
        energy.some((e, i) => !Number.isFinite(e) || e <= 0 || (i && e <= energy[i - 1])) ||
        absorption.some((a) => !Number.isFinite(a) || a < 0) ||
        energy[0] > HC / 780 || energy.at(-1) < HC / 380) return null;

    // Interpolate the energy-domain absorption at E = hc/lambda. Absorbance is
    // not a probability density: no wavelength Jacobian or peak normalization.
    const sample = (e) => {
      let lo = 0, hi = energy.length - 1;
      while (hi - lo > 1) {
        const mid = (lo + hi) >> 1;
        if (energy[mid] <= e) lo = mid; else hi = mid;
      }
      const t = (e - energy[lo]) / (energy[hi] - energy[lo]);
      return absorption[lo] * (1 - t) + absorption[hi] * t;
    };
    const xyz = [0, 0, 0];
    let referenceY = 0;
    const rows = globalThis.CIEColorData;
    rows.forEach(([nm, light, x, y, z], i) => {
      const weight = (i === 0 || i === rows.length - 1) ? 0.5 : 1;
      const transmitted = 10 ** (-density * sample(HC / nm));
      referenceY += weight * light * y;
      [x, y, z].forEach((value, channel) => {
        xyz[channel] += weight * light * transmitted * value;
      });
    });
    const [x, y, z] = xyz.map((v) => v / referenceY);
    // D65 XYZ -> linear sRGB, then clip display gamut and apply sRGB encoding.
    // Preserve luminance: do not normalize each solution to its brightest channel.
    const linear = [
      3.2406 * x - 1.5372 * y - 0.4986 * z,
      -0.9689 * x + 1.8758 * y + 0.0415 * z,
      0.0557 * x - 0.2040 * y + 1.0570 * z,
    ];
    const rgb = linear.map((v) => Math.round(255 * encode(Math.max(0, Math.min(1, v)))));
    return {rgb, css: `rgb(${rgb.join(", ")})`, luminance: y};
  }
  globalThis.SolutionColor = {estimate};
})();
