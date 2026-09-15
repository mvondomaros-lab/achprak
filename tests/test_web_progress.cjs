const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
require("../src/achprak/web/static/progress.js");
const progress = globalThis.OptimizationProgress;
const record = (step, phase = "optimization") => ({
  source_id: "source",
  step,
  phase,
  positions: [step, 0, 0],
  energy_ev: -10 - step / 10,
  fmax_ev_angstrom: 1 / (step + 1),
});
const line = (r) => "ACHPRAK_PROGRESS " + JSON.stringify(r);

test("all steps between polls are collected, partial writes retried, duplicate polls deduplicated", () => {
  const log =
    "Sella: 0\n" +
    [0, 1, 2].map((s) => line(record(s))).join("\n") +
    '\nACHPRAK_PROGRESS {"step":3';
  const parsed = progress.parse(log);
  assert.deepEqual(
    parsed.records.map((r) => r.step),
    [0, 1, 2],
  );
  assert.equal(parsed.output, "Sella: 0");
  const next = progress.parse([2, 3, 4].map((s) => line(record(s))).join("\n"));
  assert.deepEqual(
    progress.merge(parsed.records, next.records).map((r) => r.step),
    [0, 1, 2, 3, 4],
  );
});

test("terminal full history restores steps dropped by the bounded log; vibration phase adds no phantom energy point", () => {
  const tail = progress.parse(
    'truncated "positions": [0,0,0]}\n' + line(record(4)),
  ).records;
  const complete = progress.merge(
    tail,
    [0, 1, 2, 3, 4].map((s) => record(s)).concat(record(4, "vibrations")),
  );
  assert.deepEqual(
    complete.map((r) => r.step),
    [0, 1, 2, 3, 4],
  );
  assert.equal(complete.at(-1).phase, "vibrations");
  assert.equal(
    progress.parse(line({ ...record(5), energy_ev: null })).records.length,
    0,
  );
});

test("instant completion receives a paced, explicitly labeled geometry replay before result refresh", async () => {
  const records = [0, 1, 2, 3].map((s) => record(s));
  const elements = new Map();
  const seen = [];
  const context = vm.createContext({
    OptimizationProgress: progress,
    state: { tracking: { records, visibleSince: null } },
    performance: { now: () => 5000 },
    matchMedia: () => ({ matches: false }),
    $: (id) => {
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    },
    applyLiveGeometry: () => seen.push(context.state.live),
    renderEnergyHistory: () => {},
    fmt: String,
    setTimeout: (done, delay) => {
      assert.ok(delay > 0 && delay <= 180);
      done();
    },
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("async function replayShortRun()"),
      app.indexOf("function applyLiveGeometry()"),
    ),
    context,
  );
  await context.replayShortRun();
  assert.deepEqual(
    seen.map((r) => r.step),
    [0, 1, 2, 3],
  );
  assert.ok(seen.every((r) => r.replay));
  assert.match(
    elements.get("job-title").textContent,
    /abgeschlossen.*wiedergegeben/,
  );
  assert.equal(context.state.replaying, false);
  assert.equal(elements.get("skip-replay").hidden, true);
  assert.equal(progress.shouldReplay(records, 100, 5000), false);
});

test("reduced motion disables automatic replay while retaining all chart data", async () => {
  const records = [record(0), record(1)];
  const context = vm.createContext({
    OptimizationProgress: progress,
    state: { tracking: { records, visibleSince: null } },
    performance: { now: () => 500 },
    matchMedia: () => ({ matches: true }),
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("async function replayShortRun()"),
      app.indexOf("function applyLiveGeometry()"),
    ),
    context,
  );
  await context.replayShortRun();
  assert.equal(context.state.live, undefined);
  assert.equal(context.state.tracking.records.length, 2);
});

test("one playback control selects search frames or TS vibration frames", () => {
  const records = [record(0), record(1)];
  const molecule = {
    trajectory_kind: "vibration",
    frames: [
      [5, 0, 0],
      [6, 0, 0],
    ],
  };
  const search = progress.playback(molecule, records, "optimization");
  assert.deepEqual(
    search.frames,
    records.map((r) => r.positions),
  );
  assert.equal(search.kind, "optimization");
  assert.deepEqual(
    progress.playback(molecule, records, "vibration").frames,
    molecule.frames,
  );
  assert.equal(
    progress.playback(molecule, [], "optimization").kind,
    "vibration",
  );
  assert.deepEqual(
    progress.playback(
      { trajectory_kind: "optimization", frames: [[1, 2, 3]] },
      [],
      "optimization",
    ).frames,
    [[1, 2, 3]],
  );
});

test("Play resumes paused and selected steps, synchronizes geometry and energy, and never loops", () => {
  const records = [record(0), record(1), record(2)];
  const elements = new Map();
  const timers = new Map();
  const geometries = [],
    energies = [];
  let timerId = 0;
  const context = vm.createContext({
    OptimizationProgress: progress,
    state: {
      selected: "result",
      step: "optimize",
      busy: false,
      mode: "3d",
      playbackMode: "optimization",
      previewIndex: null,
    },
    component: {},
    animation: null,
    current: () => ({ trajectory_kind: "optimization" }),
    energyRecords: () => records,
    $: (id) => {
      if (!elements.has(id))
        elements.set(id, {
          style: {},
          classList: { toggle() {} },
          setAttribute() {},
          querySelector() {
            return {};
          },
        });
      return elements.get(id);
    },
    applyLiveGeometry: () => geometries.push(context.state.live.positions),
    renderEnergyHistory: (step) => energies.push(step),
    renderState: () => {
      context.updateMode();
      geometries.push(records.at(-1).positions);
      energies.push(records.at(-1).step);
    },
    setInterval: (callback) => {
      timers.set(++timerId, callback);
      return timerId;
    },
    clearInterval: (id) => timers.delete(id),
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("function stopAnimation()"),
      app.indexOf("function ensureStage()"),
    ),
    context,
  );
  vm.runInContext(
    app.slice(
      app.indexOf("function selectPlaybackFrame("),
      app.indexOf('$("xyz-download").onclick'),
    ),
    context,
  );
  vm.runInContext(
    app.slice(
      app.indexOf("function updateMode()"),
      app.indexOf("function updateControls()"),
    ),
    context,
  );
  const play = elements.get("play");
  const tick = () => [...timers.values()][0]();
  play.onclick();
  assert.equal(context.state.previewIndex, 0);
  tick();
  play.onclick(); // Pause at step 1.
  assert.equal(context.state.previewIndex, 1);
  assert.equal(timers.size, 0);
  play.onclick();
  assert.equal(context.state.previewIndex, 1);
  tick();
  assert.equal(context.state.previewIndex, null);
  assert.equal(timers.size, 0);
  assert.equal(play.textContent, "Abspielen");
  assert.equal(context.state.live, null);
  assert.equal(elements.get("properties-grid").style.visibility, "visible");
  assert.equal(elements.get("properties-context").style.visibility, "visible");
  assert.deepEqual(energies, [0, 1, 1, 2]);
  assert.deepEqual(
    geometries,
    [0, 1, 1, 2].map((i) => records[i].positions),
  );
  play.onclick(); // Explicit Play at the end restarts, but playback never loops itself.
  assert.equal(context.state.previewIndex, 0);
  assert.equal(timers.size, 1);
  tick();
  tick();
  assert.equal(context.state.previewIndex, null);
  assert.equal(timers.size, 0);
  context.selectPlaybackFrame(2);
  play.onclick(); // The same applies to a manually selected final frame.
  assert.equal(context.state.previewIndex, 0);
  play.onclick(); // Pause before testing intermediate-step resume.

  context.selectPlaybackFrame(1);
  play.onclick(); // Resume from the manually selected step.
  assert.equal(context.state.previewIndex, 1);
  tick();
  assert.equal(context.state.previewIndex, null);
  assert.equal(timers.size, 0);

  context.selectPlaybackFrame(0);
  play.onclick();
  tick();
  context.selectPlaybackFrame(0); // Scrubbing pauses ongoing playback.
  assert.equal(timers.size, 0);
  play.onclick();
  assert.equal(context.state.previewIndex, 0);
  tick();
  tick();
  assert.equal(timers.size, 0);
});

test("TS scan, refinement and all-atom validation keep one continuous energy history", () => {
  const records = [
    record(0, "path_seed"),
    record(1, "path_seed"),
    record(2, "refinement"),
    record(2, "vibrations"),
  ];
  const parsed = progress.parse(records.map(line).join("\n"));
  assert.equal(parsed.records.length, 4);
  const history = progress.merge([], parsed.records);
  assert.deepEqual(
    history.map((r) => r.step),
    [0, 1, 2],
  );
  assert.equal(history.at(-1).phase, "vibrations");
});

test("NEB snapshots survive polling and reaction-path playback remains separate from iterations", () => {
  const path = [0, 1, 2].map((i) => ({
    image: i,
    coordinate: i / 2,
    positions: [i, 0, 0],
    energy_ev: [-10, -8, -9][i],
  }));
  const r = { ...record(12, "neb_climb"), neb_path: path };
  const parsed = progress.parse(
    "ACHPRAK_PROGRESS " + JSON.stringify(r) + "\n",
  ).records;
  assert.deepEqual(parsed, [r]);
  const molecule = {
    id: "m",
    trajectory_kind: "vibration",
    frames: [[0, 0, 0]],
    ts_search: { path },
  };
  const playback = progress.playback(molecule, parsed, "path");
  assert.equal(playback.kind, "path");
  assert.deepEqual(
    playback.frames,
    path.map((p) => p.positions),
  );
  assert.deepEqual(
    playback.records.map((p) => p.coordinate),
    [0, 0.5, 1],
  );
  assert.equal(
    progress.playback(molecule, parsed, "optimization").records[0].step,
    12,
  );
  assert.equal(
    progress.playback(molecule, parsed, "vibration").kind,
    "vibration",
  );
});

test("energy chart switches between reaction coordinate and iteration history without mixing axes", () => {
  const path = [0, 1, 2].map((i) => ({
    image: i,
    coordinate: i / 2,
    positions: [i, 0, 0],
    energy_ev: [-10, -8, -9][i],
  }));
  const records = [
    { ...record(0, "endpoint"), energy_ev: -10 },
    { ...record(8, "neb_climb"), energy_ev: -10, neb_path: path, neb_image: 0 },
    { ...record(9, "vibrations"), energy_ev: -8 },
  ];
  const m = { id: "m", ts_search: { path }, optimization_history: records };
  const elements = new Map();
  let chart;
  const context = vm.createContext({
    OptimizationProgress: progress,
    state: {
      step: "optimize",
      selected: "m",
      busy: false,
      playbackMode: "path",
      live: null,
    },
    current: () => m,
    fmt: String,
    $: (id) => {
      if (!elements.has(id)) elements.set(id, { setAttribute() {} });
      return elements.get(id);
    },
    Chart: class {
      constructor(_, config) {
        Object.assign(this, config);
        chart = this;
      }
      update() {}
    },
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("let energyChart = null;"),
      app.indexOf("function collectProgress("),
    ),
    context,
  );
  context.renderEnergyHistory();
  assert.deepEqual(
    Array.from(chart.data.datasets[0].data, (p) => p.x),
    [0, 0.5, 1],
  );
  assert.match(chart.options.scales.x.title.text, /Ausgangsform/);
  context.state.live = { ...path[1], phase: "path" };
  context.renderEnergyHistory(1);
  assert.equal(chart.data.datasets[1].data[0].x, 0.5);
  context.state.live = null;
  context.state.playbackMode = "optimization";
  context.renderEnergyHistory(8);
  assert.deepEqual(
    Array.from(chart.data.datasets[0].data, (p) => p.x),
    [0, 8, 9],
  );
  assert.equal(chart.options.scales.x.title.text, "Optimierungsschritt");
  context.state.busy = true;
  context.state.tracking = { sourceId: "m", status: "running", records };
  context.renderEnergyHistory(8);
  assert.equal(chart.data.datasets[1].data[0].image, 0);
  context.renderEnergyHistory(9);
  assert.deepEqual(
    Array.from(chart.data.datasets[0].data, (p) => p.x),
    [0, 0.5, 1],
  );
  context.state.busy = false;
  context.state.playbackMode = "vibration";
  context.state.live = { phase: "vibration-preview" };
  context.renderEnergyHistory();
  assert.equal(chart.data.datasets[1].data.length, 0);
});

test("live NEB coordinates reach the 3D viewer and identify the displayed image", () => {
  const positions = [];
  const elements = new Map();
  const context = vm.createContext({
    Float32Array,
    OptimizationProgress: progress,
    fmt: String,
    state: {
      step: "optimize",
      busy: true,
      mode: "3d",
      live: {
        ...record(1, "neb"),
        source_id: "m",
        positions: [1, 0, 0],
        neb_image: 3,
      },
    },
    current: () => ({ id: "m" }),
    stopAnimation() {},
    renderPlaybackControls() {},
    component: {
      structure: {
        atomCount: 1,
        updatePosition: (p) => positions.push(Array.from(p)),
      },
      updateRepresentations() {},
    },
    $: (id) => {
      if (!elements.has(id))
        elements.set(id, { style: {}, classList: { remove() {} } });
      return elements.get(id);
    },
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("function applyLiveGeometry()"),
      app.indexOf("function displayJob("),
    ),
    context,
  );
  context.applyLiveGeometry();
  context.state.live.positions = [2, 0, 0];
  context.applyLiveGeometry();
  assert.deepEqual(positions, [
    [1, 0, 0],
    [2, 0, 0],
  ]);
  assert.equal(
    elements.get("geometry-badge").textContent,
    "Live · Struktur auf dem Reaktionspfad 4",
  );
  assert.equal(elements.get("image-download").disabled, false);
  context.state.live.source_id = "another-molecule";
  context.applyLiveGeometry();
  assert.equal(positions.length, 2);
  assert.equal(elements.get("properties-grid").style.visibility, "visible");
  assert.equal(
    elements.get("energy").textContent,
    String(context.state.live.energy_ev),
  );
  context.state.live.source_id = "m";
  context.state.live.phase = "vibration-preview";
  context.applyLiveGeometry();
  assert.equal(elements.get("energy").textContent, "—");
});

test("same molecule reuses its viewer and restores result positions without resetting the camera", async () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const elements = new Map();
  const positions = [];
  let loads = 0,
    cameraChanges = 0;
  const molecule = { id: "m", svg: "svg", xyz: "1\nresult\nH 1 2 3\n" };
  const context = vm.createContext({
    Float32Array,
    Blob,
    state: { mode: "3d", step: "optimize", live: null },
    renderVersion: 0,
    renderedMolecule: "m",
    loadingMolecule: null,
    current: () => molecule,
    svgURL: (s) => s,
    component: {
      structure: { updatePosition: (p) => positions.push(Array.from(p)) },
      updateRepresentations() {},
      autoView() {
        cameraChanges++;
      },
    },
    stage: {
      handleResize() {},
      removeAllComponents() {
        throw Error("Unexpected teardown");
      },
    },
    ensureStage: () => ({
      loadFile() {
        loads++;
      },
    }),
    applyLiveGeometry() {},
    renderPlaybackControls() {},
    $: (id) => {
      if (!elements.has(id))
        elements.set(id, {
          getAttribute() {
            return this.src;
          },
        });
      return elements.get(id);
    },
  });
  vm.runInContext(
    app.slice(
      app.indexOf("function restoreResultGeometry()"),
      app.indexOf("function updateMode()"),
    ),
    context,
  );
  await context.renderMolecule();
  context.state.mode = "2d";
  await context.renderMolecule();
  context.state.mode = "3d";
  await context.renderMolecule();
  context.state.step = "spectrum";
  await context.renderMolecule();
  context.state.step = "build";
  await context.renderMolecule();
  assert.equal(loads, 0);
  assert.equal(cameraChanges, 0);
  assert.deepEqual(positions, [
    [1, 2, 3],
    [1, 2, 3],
    [1, 2, 3],
  ]);
});

test("playback appears when frames exist and the mode picker is hidden without alternatives", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const elements = new Map();
  let frames = [];
  const context = vm.createContext({
    state: { step: "optimize", busy: false, mode: "3d", previewIndex: null },
    component: {},
    current: () => ({ kind: "minimum" }),
    energyRecords: () => [],
    playbackData: () => ({ kind: "optimization", frames, records: [] }),
    $: (id) => {
      if (!elements.has(id))
        elements.set(id, { querySelector: () => ({}), setAttribute() {} });
      return elements.get(id);
    },
  });
  vm.runInContext(
    app.slice(
      app.indexOf("function renderPlaybackControls()"),
      app.indexOf("function showFrame("),
    ),
    context,
  );
  for (const phase of ["empty", "running", "result", "2d", "build"]) {
    context.state.step = phase === "build" ? "build" : "optimize";
    context.state.busy = phase === "running";
    context.state.mode = phase === "2d" ? "2d" : "3d";
    frames =
      phase === "empty"
        ? []
        : [
            [0, 0, 0],
            [1, 0, 0],
          ];
    context.renderPlaybackControls();
    assert.equal(
      elements.get("trajectory").hidden,
      ["build", "empty"].includes(phase),
    );
    assert.equal(elements.get("playback-mode").hidden, true);
    assert.equal(
      elements.get("play").disabled,
      !["result", "build"].includes(phase),
    );
    assert.equal(
      elements.get("play").disabled,
      !["result", "build"].includes(phase),
    );
  }
});

test("known starting energy is shown before progress without creating playback frames", () => {
  const elements = new Map();
  const m = { id: "m", properties: { energy_ev: -10 } };
  let chart;
  const context = vm.createContext({
    OptimizationProgress: progress,
    state: {
      step: "optimize",
      selected: "m",
      busy: false,
      playbackMode: "optimization",
    },
    current: () => m,
    fmt: String,
    $: (id) => {
      if (!elements.has(id)) elements.set(id, { setAttribute() {} });
      return elements.get(id);
    },
    Chart: class {
      constructor(_, config) {
        Object.assign(this, config);
        chart = this;
      }
      update() {}
    },
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("let energyChart = null;"),
      app.indexOf("function collectProgress("),
    ),
    context,
  );
  context.renderEnergyHistory();
  assert.equal(elements.get("energy-history").hidden, false);
  assert.match(
    elements.get("energy-history-value").textContent,
    /Ausgangsenergie: -10/,
  );
  assert.equal(chart.data.datasets[1].data[0].y, 0);
  assert.equal(context.energyRecords().length, 0);
  const original = chart;
  context.state.busy = true;
  context.state.tracking = {
    sourceId: "m",
    status: "running",
    records: [
      { ...record(0), energy_ev: -10 },
      { ...record(1), energy_ev: -11 },
    ],
  };
  context.renderEnergyHistory();
  assert.equal(chart, original);
  assert.equal(chart.data.datasets[0].data.length, 2);
  assert.equal(chart.data.datasets[1].data[0].y, -1);
  context.state.step = "build";
  context.renderEnergyHistory();
  assert.equal(elements.get("energy-history").hidden, true);
  context.state.step = "optimize";
  context.renderEnergyHistory();
  assert.equal(elements.get("energy-history").hidden, false);
});

test("plot clicks select the matching structure, including reaction paths, and ignore unavailable interactions", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const selected = [];
  const context = vm.createContext({
    state: {
      busy: false,
      mode: "3d",
      step: "optimize",
      playbackMode: "optimization",
    },
    component: {},
    playbackData: () => ({
      records:
        context.state.playbackMode === "path"
          ? [{ image: 2 }, { image: 5 }, { image: 9 }]
          : [{ step: 0 }, { step: 4 }, { step: 10 }],
    }),
    selectPlaybackFrame: (index) => selected.push(index),
  });
  vm.runInContext(
    app.slice(
      app.indexOf("function selectEnergyPoint("),
      app.indexOf("function renderEnergyHistory("),
    ),
    context,
  );
  const chart = {
    chartArea: { left: 0, right: 100, top: 0, bottom: 100 },
    scales: { x: { getValueForPixel: (x) => x } },
    data: {
      datasets: [
        {
          data: [
            { x: 0, y: 0 },
            { x: 4, y: -1 },
            { x: 10, y: -2 },
          ],
        },
      ],
    },
  };
  context.selectEnergyPoint({ x: 3, y: 50 }, [], chart);
  context.selectEnergyPoint({ x: 10, y: 50 }, [], chart);
  assert.deepEqual(selected, [1, 2]);
  context.state.playbackMode = "vibration";
  chart.data.datasets[0].data = [
    { x: 0, y: 0, image: 2, phase: "path" },
    { x: 0.5, y: 1, image: 5, phase: "path" },
    { x: 1, y: 0, image: 9, phase: "path" },
  ];
  context.selectEnergyPoint({ x: 0.6, y: 50 }, [], chart);
  assert.equal(context.state.playbackMode, "path");
  assert.deepEqual(selected, [1, 2, 1]);
  context.state.busy = true;
  context.selectEnergyPoint({ x: 1, y: 50 }, [], chart);
  context.state.busy = false;
  context.selectEnergyPoint({ x: -1, y: 50 }, [], chart);
  context.state.mode = "2d";
  context.selectEnergyPoint({ x: 1, y: 50 }, [], chart);
  assert.equal(selected.length, 3);
});

test("intermediate geometry properties use the shown positions and mass-weighted ring centers", () => {
  const definition = {
    dihedral_indices: [0, 1, 2, 3],
    rings: [
      [0, 1],
      [2, 3],
    ],
    masses: [1, 3, 1, 3],
  };
  const positions = [0, 1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1];
  const props = progress.geometryProperties(positions, definition);
  assert.equal(props.dihedral_deg, 90);
  assert.ok(
    Math.abs(
      props.ring_distance_pm - Math.sqrt(1 + 0.25 ** 2 + 0.75 ** 2) * 100,
    ) < 1e-9,
  );
  const translated = positions.map((x, i) => x + [3, 5, 7][i % 3]);
  assert.deepEqual(progress.geometryProperties(translated, definition), props);
  const rotated = [...positions];
  rotated[11] = -1;
  assert.equal(
    progress.geometryProperties(rotated, definition).dihedral_deg,
    270,
  );
  const linear = [...positions];
  linear[1] = 0;
  assert.equal(
    progress.geometryProperties(linear, definition).dihedral_deg,
    null,
  );
});

test("result tools appear only when useful and spectrum prerequisites remain enforced", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const elements = new Map();
  let molecule;
  let target = "minimum";
  const context = vm.createContext({
    state: { busy: false, molecules: [], step: "build", live: null, job: null },
    current: () => molecule,
    document: { querySelector: () => ({ value: target }) },
    updateMode() {},
    $: (id) => {
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    },
  });
  vm.runInContext(
    app.slice(
      app.indexOf("function updateControls()"),
      app.indexOf("function renderSpectrum()"),
    ),
    context,
  );
  context.updateControls();
  for (const id of [
    "structure-library",
    "result-heading",
    "viewer-toolbar",
    "result-details",
  ])
    assert.equal(elements.get(id).hidden, true);
  assert.equal(elements.get("calculate-spectrum").disabled, true);

  molecule = { kind: "initial" };
  context.state.molecules = [molecule];
  context.state.step = "optimize";
  target = "ts";
  context.updateControls();
  assert.equal(elements.get("result-heading").hidden, false);
  assert.equal(elements.get("ts-requirement").hidden, false);
  assert.equal(elements.get("optimize").disabled, true);
  assert.equal(elements.get("trajectory-download").hidden, true);

  molecule.kind = "minimum";
  target = "minimum";
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, true);
  target = "ts";
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, false);
  context.state.step = "spectrum";
  context.updateControls();
  assert.equal(elements.get("calculate-spectrum").disabled, false);
  assert.equal(elements.get("spectrum-requirement").hidden, true);
  assert.equal(elements.get("coordinate-details").hidden, true);
  context.state.busy = true;
  context.updateControls();
  assert.equal(elements.get("calculate-spectrum").disabled, true);
});

test("structure step shows only the 2D formula without properties or calculation tools", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const elements = new Map();
  const context = vm.createContext({
    state: {
      step: "build",
      mode: "3d",
      molecules: [{ id: "m" }],
      hasCalculationLog: true,
    },
    current: () => ({ id: "m", kind: "initial" }),
    document: { querySelector: () => ({ value: "minimum" }) },
    renderPlaybackControls() {},
    stopAnimation() {},
    $: (id) => {
      if (!elements.has(id))
        elements.set(id, {
          style: {},
          classList: { toggle() {} },
          setAttribute() {},
        });
      return elements.get(id);
    },
  });
  vm.runInContext(
    app.slice(
      app.indexOf("function updateMode()"),
      app.indexOf("function renderSpectrum()"),
    ),
    context,
  );
  context.updateControls();
  assert.equal(context.state.mode, "2d");
  assert.equal(elements.get("structure-image").hidden, false);
  for (const id of [
    "viewport",
    "center",
    "properties-grid",
    "properties-context",
    "property-help",
    "result-details",
    "calculation-log",
  ])
    assert.equal(elements.get(id).hidden, true, id);
  assert.equal(elements.get("image-download").disabled, false);
});

test("image export pauses playback and captures the displayed intermediate geometry", async () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const button = {};
  const calls = [];
  const context = vm.createContext({
    state: { mode: "3d", previewIndex: 3, live: { positions: [1, 2, 3] } },
    component: {},
    $: () => button,
    handle: (fn) => fn,
    stopAnimation: () => calls.push("pause"),
    filename: (ext) => `structure.${ext}`,
    stage: {
      makeImage: async () => {
        calls.push("capture");
        return "intermediate image";
      },
    },
    download: (image, name) => calls.push([image, name]),
  });
  vm.runInContext(
    app.slice(
      app.indexOf('$("image-download").onclick'),
      app.indexOf('$("spectrum-svg").onclick'),
    ),
    context,
  );
  await button.onclick();
  assert.deepEqual(calls, [
    "pause",
    "capture",
    ["intermediate image", "structure.png"],
  ]);
  assert.equal(context.state.previewIndex, 3);
  assert.deepEqual(context.state.live.positions, [1, 2, 3]);
});
