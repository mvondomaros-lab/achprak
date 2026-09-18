const test = require("node:test");
const assert = require("node:assert/strict");
require("../src/achprak/web/static/vendor/cie-color.js");
require("../src/achprak/web/static/solution-color.js");
const estimate = globalThis.SolutionColor.estimate;
const flat = (a) => ({ energy_ev: [1.5, 5.5], absorption: [a, a], coverage_complete: true });

test("unabsorbed D65 is white", () => {
  const result = estimate(flat(0));
  assert.deepEqual(result.rgb, [255, 255, 255]);
  assert.ok(Math.abs(result.luminance - 1) < 1e-12);
});

test("neutral absorption follows Beer–Lambert transmission without brightness normalization", () => {
  const result = estimate(flat(1));
  assert.ok(Math.abs(result.luminance - 0.1) < 1e-12);
  for (const channel of result.rgb) assert.ok(Math.abs(channel - 89) <= 1);
});

test("selective blue absorption gives a yellow transmitted color", () => {
  const energy_ev = Array.from({length: 1000}, (_, i) => 1.5 + i * 4 / 999);
  const absorption = energy_ev.map((e) => 2 * Math.exp(-0.5 * ((e - 2.75) / 0.23) ** 2));
  const result = estimate({energy_ev, absorption});
  assert.ok(result.rgb[0] > result.rgb[2] + 100);
  assert.ok(result.rgb[1] > result.rgb[2] + 100);
});

test("missing coverage and invalid data never produce a misleading swatch", () => {
  for (const spec of [null, {}, {...flat(1), coverage_complete: false},
    {energy_ev: [2, 3], absorption: [1, 1]},
    {energy_ev: [5.5, 1.5], absorption: [1, 1]},
    {energy_ev: [1.5, 5.5], absorption: [NaN, 1]},
    {energy_ev: [1.5, 5.5], absorption: [-1, 1]},
    {energy_ev: [1.5, 5.5], absorption: [1]}]) assert.equal(estimate(spec), null);
});

test("structure changes refresh the swatch and clear unavailable results", () => {
  const fs = require("node:fs"), vm = require("node:vm");
  const elements = {};
  const get = (id) => elements[id] ||= {
    value: "1", style: {}, setAttribute(key, value) { this[key] = value; },
    addEventListener(event, callback) { this[event] = callback; },
  };
  let molecule = {label: "trans · H", spectrum: flat(0)};
  const context = vm.createContext({
    $: get, current: () => molecule, SolutionColor: globalThis.SolutionColor,
    structureLabel: (m) => m.label,
    fmt: (v, n) => v.toFixed(n).replace(".", ","),
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(app.slice(app.indexOf("function renderSolutionColor()"), app.indexOf("function renderState()")), context);
  context.renderSolutionColor();
  assert.equal(get("solution-color-swatch").style.backgroundColor, "rgb(255, 255, 255)");
  molecule = {label: "cis · 4-OMe", spectrum: flat(1)};
  context.renderSolutionColor();
  assert.match(get("solution-color-swatch")["aria-label"], /cis · 4-OMe/);
  assert.match(get("solution-color-status").textContent, /10,0 %/);
  molecule.spectrum.coverage_complete = false;
  context.renderSolutionColor();
  assert.equal(get("solution-color-swatch").hidden, true);
  assert.equal(get("solution-color-swatch").style.backgroundColor, "");
  assert.match(get("solution-color-status").textContent, /Keine Farbschätzung/);
});
