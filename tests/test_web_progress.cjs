const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
function loadSelectionFunctions(context) {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("function selectableMolecules()"),
      app.indexOf("const fmt ="),
    ),
    context,
  );
}
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

test("short optimizations load the result directly without automatic playback", async () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  for (const kind of ["minimum", "ts"]) {
    const events = [];
    const records = [record(0), record(1)];
    const job = { status: "complete", kind, result: { molecule: { id: "result" } } };
    const context = vm.createContext({
      state: { tracking: { records }, live: record(1) },
      api: async () => job,
      updateControls: () => {},
      displayJob: () => events.push("status"),
      refresh: async (id, completed) => {
        assert.equal(id, "result");
        assert.equal(completed, true);
        events.push("result");
        context.state.live = null;
      },
      renderEnergyHistory: () => {},
      error: (message) => assert.fail(message),
    });
    vm.runInContext(app.slice(app.indexOf("async function monitor("), app.indexOf("async function startJob(")), context);
    await context.monitor("job");
    assert.deepEqual(events, ["status", "result", "status"]);
    assert.equal(context.state.busy, false);
    assert.equal(context.state.tracking.records.length, 2);
  }
});

test("playback uses recorded steps and falls back to stored optimization frames", () => {
  const records = [record(0), record(1)];
  const molecule = { frames: [[5, 0, 0], [6, 0, 0]] };
  const search = progress.playback(molecule, records, "optimization");
  assert.deepEqual(search.frames, records.map((r) => r.positions));
  assert.equal(search.kind, "optimization");
  assert.deepEqual(progress.playback(molecule, [], "optimization").frames, molecule.frames);
  assert.deepEqual(progress.playback(null, [], "optimization").frames, []);
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
      previewIndex: null,
    },
    component: {},
    animation: null,
    current: () => ({ ts_search: { path: records.map((p, i) => ({ ...p, image: i, coordinate: i / 2 })) } }),
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
          prepend(child) {
            child.parentElement = this;
          },
          append(child) {
            child.parentElement = this;
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
      app.indexOf("async function svgToPNG"),
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
  const energyPlay = elements.get("energy-play");
  assert.equal(energyPlay.onclick, play.onclick);
  const tick = () => [...timers.values()][0]();
  play.onclick();
  assert.equal(energyPlay.textContent, "Pause");
  assert.equal(context.state.previewIndex, 0);
  tick();
  energyPlay.onclick(); // The repeated button pauses the same playback.
  assert.equal(play.textContent, "Abspielen");
  assert.equal(energyPlay.textContent, "Abspielen");
  assert.equal(context.state.previewIndex, 1);
  assert.equal(timers.size, 0);
  play.onclick();
  assert.equal(context.state.previewIndex, 1);
  tick();
  assert.equal(context.state.previewIndex, 2);
  assert.equal(timers.size, 0);
  assert.equal(play.textContent, "Abspielen");
  assert.equal(context.state.live.phase, "path");
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
  assert.equal(context.state.previewIndex, 2);
  assert.equal(timers.size, 0);
  context.selectPlaybackFrame(2);
  play.onclick(); // The same applies to a manually selected final frame.
  assert.equal(context.state.previewIndex, 0);
  play.onclick(); // Pause before testing intermediate-step resume.

  context.selectPlaybackFrame(1);
  play.onclick(); // Resume from the manually selected step.
  assert.equal(context.state.previewIndex, 1);
  tick();
  assert.equal(context.state.previewIndex, 2);
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
});

test("energy chart shows only reaction coordinates and describes the path", () => {
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
  const m = { id: "m", base_name: "trans-Azobenzol", ts_search: { path }, optimization_history: records };
  const elements = new Map();
  let chart;
  const context = vm.createContext({
    OptimizationProgress: progress,
    state: {
      step: "optimize",
      selected: "m",
      busy: false,
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
  assert.equal(chart.options.scales.x.title.text, "Reaktionspfad");
  context.state.live = { ...path[1], phase: "path" };
  context.renderEnergyHistory(1);
  assert.equal(chart.data.datasets[1].data[0].x, 0.5);
  context.state.live = null;
  context.renderEnergyHistory(8);
  assert.deepEqual(
    Array.from(chart.data.datasets[0].data, (p) => p.x),
    [0, 0.5, 1],
  );
  assert.equal(chart.options.scales.x.title.text, "Reaktionspfad");
  assert.equal(elements.get("energy-path-meta").textContent, "Reaktionspfad im elektronischen Grundzustand · trans → cis");
  context.state.busy = true;
  context.state.tracking = { sourceId: "m", kind: "ts", status: "queued", records: [] };
  context.renderEnergyHistory();
  assert.equal(elements.get("energy-history").hidden, false);
  assert.equal(chart.data.datasets[0].data.length, 0);
  context.state.tracking.status = "running";
  context.state.tracking.records = [records[0], { ...record(1, "path_seed"), energy_ev: -9 }];
  context.renderEnergyHistory(1);
  assert.equal(elements.get("energy-history").hidden, false);
  assert.equal(chart.options.scales.x.title.text, "Suchschritt");
  assert.deepEqual(Array.from(chart.data.datasets[0].data, (p) => p.y), [0, 1]);
  assert.match(elements.get("energy-reference").textContent, /noch kein Reaktionspfad/);
  context.state.tracking.records = records;
  context.renderEnergyHistory(8);
  assert.equal(chart.data.datasets[1].data[0].image, 0);
  context.renderEnergyHistory(9);
  assert.deepEqual(
    Array.from(chart.data.datasets[0].data, (p) => p.x),
    [0, 0.5, 1],
  );
  context.state.busy = false;
  context.state.live = null;
  context.renderEnergyHistory();
  assert.equal(chart.data.datasets[1].data.length, 1);
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
        elements.set(id, { style: {}, classList: {
          remove() {},
          toggle(name, enabled) { this[name] = enabled; },
        } });
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
    elements.get("properties-context").textContent,
    "Berechnung läuft · Werte der Struktur auf dem Reaktionspfad 4",
  );
  assert.equal(elements.get("geometry-badge").hidden, false);
  assert.equal(elements.get("geometry-badge").textContent, "Live");
  assert.equal(elements.get("geometry-badge").classList.live, true);
  assert.equal(elements.get("geometry-badge").classList.playback, false);
  context.state.live.replay = true;
  context.applyLiveGeometry();
  assert.equal(elements.get("properties-context").textContent,
    "Wiedergabe · Werte der Struktur auf dem Reaktionspfad 4");
  assert.equal(elements.get("geometry-badge").textContent, "Wiedergabe");
  assert.equal(elements.get("geometry-badge").classList.live, false);
  assert.equal(elements.get("geometry-badge").classList.playback, true);
  assert.equal(elements.get("image-download").disabled, false);
  context.state.live.source_id = "another-molecule";
  context.applyLiveGeometry();
  assert.equal(positions.length, 3);
  assert.equal(elements.get("properties-grid").style.visibility, "visible");
  assert.equal(
    elements.get("energy").textContent,
    String(context.state.live.energy_ev),
  );
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

test("both playback buttons appear only when frames exist", () => {
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
      elements.get("play").hidden,
      ["build", "empty"].includes(phase),
    );
    assert.equal(elements.get("energy-play").hidden, ["build", "empty"].includes(phase));
    assert.equal(
      elements.get("energy-play").disabled,
      !["result", "build"].includes(phase),
    );
    assert.equal(
      elements.get("play").disabled,
      !["result", "build"].includes(phase),
    );
  }
});

test("minimum energy history appears live and remains available after completion", () => {
  const elements = new Map();
  const m = { id: "m", properties: { energy_ev: -10 } };
  let chart;
  const context = vm.createContext({
    OptimizationProgress: progress,
    state: {
      step: "optimize",
      selected: "m",
      busy: false,
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
  assert.equal(elements.get("energy-history").hidden, true);
  assert.equal(chart, undefined);
  assert.equal(context.energyRecords().length, 0);
  context.state.busy = true;
  context.state.tracking = { sourceId: "m", kind: "minimum", status: "queued", records: [] };
  context.renderEnergyHistory();
  assert.equal(elements.get("energy-history").hidden, false);
  assert.equal(chart.data.datasets[0].data.length, 0);
  const queuedChart = chart;
  context.state.tracking = {
    sourceId: "m",
    kind: "minimum",
    status: "running",
    records: [
      { ...record(0), energy_ev: -10 },
      { ...record(1), energy_ev: -11 },
    ],
  };
  context.renderEnergyHistory();
  assert.equal(elements.get("energy-history").hidden, false);
  assert.equal(chart, queuedChart);
  assert.equal(chart.options.scales.x.title.text, "Optimierungsschritt");
  assert.deepEqual(Array.from(chart.data.datasets[0].data, (p) => p.y), [0, -1]);
  assert.equal(context.energyRecords().length, 2);
  m.optimization_history = context.state.tracking.records;
  context.state.tracking.status = "complete";
  context.state.busy = false;
  context.renderEnergyHistory();
  assert.equal(elements.get("energy-history").hidden, false);
  assert.deepEqual(Array.from(chart.data.datasets[0].data, (p) => p.x), [0, 1]);
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
  let pathSelected = false;
  const context = vm.createContext({
    state: {
      busy: false,
      mode: "3d",
      step: "optimize",
    },
    component: {},
    playbackData: () => ({
      records:
        pathSelected
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
  pathSelected = true;
  chart.data.datasets[0].data = [
    { x: 0, y: 0, image: 2, phase: "path" },
    { x: 0.5, y: 1, image: 5, phase: "path" },
    { x: 1, y: 0, image: 9, phase: "path" },
  ];
  context.selectEnergyPoint({ x: 0.6, y: 50 }, [], chart);
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
  loadSelectionFunctions(context);
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

  molecule.kind = "ts";
  target = "minimum";
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, true);
  assert.equal(elements.get("ts-requirement").hidden, false);
  assert.match(elements.get("ts-requirement").textContent, /Wählen Sie eine Startstruktur/);

  molecule.kind = "minimum";
  target = "minimum";
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, true);
  target = "ts";
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, false);
  molecule.ts_restriction = "Für die Übergangszustandssuche gilt: höchstens zwei Substituenten.";
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, true);
  assert.equal(elements.get("ts-requirement").hidden, false);
  assert.equal(elements.get("ts-requirement").textContent, molecule.ts_restriction);
  assert.equal(elements.get("calculate-spectrum").disabled, false);
  molecule.kind = "initial";
  target = "minimum";
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, false);
  assert.equal(elements.get("ts-requirement").hidden, true);
  molecule.kind = "minimum";
  target = "ts";
  delete molecule.ts_restriction;
  context.updateControls();
  assert.equal(elements.get("optimize").disabled, false);
  assert.equal(elements.get("ts-requirement").hidden, true);
  context.state.step = "spectrum";
  context.updateControls();
  assert.equal(elements.get("calculate-spectrum").disabled, false);
  assert.equal(elements.get("spectrum-requirement").hidden, true);
  molecule.spectrum = { energy_ev: [2], absorption: [1] };
  context.updateControls();
  assert.equal(elements.get("calculate-spectrum").disabled, true);
  assert.equal(elements.get("calculate-spectrum").textContent, "Spektrum bereits berechnet");
  delete molecule.spectrum;
  context.updateControls();
  assert.equal(elements.get("calculate-spectrum").disabled, false);
  assert.equal(elements.get("calculate-spectrum").textContent, "Spektrum berechnen");
  context.state.busy = true;
  context.updateControls();
  assert.equal(elements.get("calculate-spectrum").disabled, true);
});

test("structure step defaults to 2D and remembers optional 3D without calculation tools", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const elements = new Map();
  const context = vm.createContext({
    state: {
      step: "build",
      mode: "3d",
      molecules: [{ id: "m", kind: "initial" }],
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
          prepend(child) {
            child.parentElement = this;
          },
          append(child) {
            child.parentElement = this;
          },
        });
      return elements.get(id);
    },
  });
  loadSelectionFunctions(context);
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
  ])
    assert.equal(elements.get(id).hidden, true, id);
  assert.equal(elements.get("image-download").disabled, false);
  context.renderState = () => context.updateControls();
  const toggleStart = app.indexOf(
    '$("build-view-toggle").onchange',
    app.indexOf('$("structure-search").oninput'),
  );
  vm.runInContext(
    app.slice(
      toggleStart,
      app.indexOf('$("clear-structures").onclick', toggleStart),
    ),
    context,
  );
  elements.get("build-view-toggle").onchange({ target: { value: "3d" } });
  assert.equal(elements.get("build-view-3d").checked, true);
  assert.equal(elements.get("build-view-2d").checked, false);
  assert.equal(context.state.mode, "3d");
  assert.equal(elements.get("viewport").hidden, false);
  assert.equal(elements.get("structure-image").hidden, true);
  assert.equal(elements.get("center").hidden, false);
  assert.equal(elements.get("center").disabled, false);
  assert.equal(elements.get("viewer-hint").hidden, false);
  for (const id of [
    "properties-grid",
  ])
    assert.equal(elements.get(id).hidden, true, id);
  context.state.step = "optimize";
  context.updateControls();
  assert.equal(elements.get("build-view-toggle").hidden, true);
  context.state.step = "build";
  context.updateControls();
  assert.equal(context.state.mode, "3d");
  elements.get("build-view-toggle").onchange({ target: { value: "2d" } });
  assert.equal(elements.get("build-view-2d").checked, true);
  assert.equal(elements.get("build-view-3d").checked, false);
  assert.equal(context.state.mode, "2d");
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
      app.indexOf('$("spectrum-png").onclick'),
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

test("structure picker groups chemical identities and keeps variants individually selectable", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const context = vm.createContext({
    KIND: {
      initial: "Startstruktur",
      minimum: "Minimum",
      ts: "Übergangszustand",
      unconverged: "Optimierung nicht abgeschlossen",
    },
  });
  vm.runInContext(app.slice(app.indexOf("function substituentLabel("), app.indexOf("for (let r =")), context);
  vm.runInContext(
    app.slice(
      app.indexOf("function structureIdentity("),
      app.indexOf("function renderStructureOptions("),
    ),
    context,
  );
  const molecules = [
    {
      id: "a",
      base_name: "cis-Azobenzol",
      formula: "C12H10N2",
      kind: "initial",
    },
    {
      id: "b",
      base_name: "cis-Azobenzol",
      formula: "C12H10N2",
      kind: "minimum",
    },
    {
      id: "c",
      base_name: "trans-Azobenzol",
      formula: "C12H10N2",
      kind: "minimum",
    },
    { id: "d", base_name: "cis-Azobenzol", formula: "C12H10N2", kind: "ts" },
    {
      id: "e",
      base_name: "cis-Azobenzol",
      formula: "C12H10N2",
      kind: "minimum",
    },
    {
      id: "f",
      base_name: "trans-2-F-Azobenzol",
      formula: "C12H9FN2",
      kind: "initial",
    },
  ];
  assert.equal(context.structureLabel(molecules[0]), "cis · unsubstituiert");
  assert.equal(context.structureGroupLabel(molecules[3]), "cis · unsubstituiert");
  assert.equal(context.structureGroupLabel({ base_name: "trans-4-OMe-Azobenzol", kind: "ts" }), "trans · 4-OMe");
  assert.equal(context.structureLabel(molecules[3]), "cis → trans Übergangszustand · unsubstituiert");
  assert.equal(context.structureLabel({ base_name: "trans-4-OMe-Azobenzol", kind: "ts" }), "trans → cis Übergangszustand · 4-OMe");
  assert.equal(context.structureLabel(molecules[5]), "trans · 2-F");
  assert.equal(context.structureLabel({ base_name: "cis-4-F, 4′-NMe2-Azobenzol", kind: "minimum" }), "cis · 4-F, 4′-NMe₂");
  assert.equal(context.structureLabel({ base_name: "trans-4-OMe-Azobenzol", kind: "unconverged", ts_search: {} }), "trans → cis · 4-OMe");
  const groups = context.structureGroups(molecules);
  assert.equal(groups.length, 3);
  assert.equal(groups[0].name, "cis · unsubstituiert");
  assert.equal(groups[1].name, "trans · unsubstituiert");
  assert.equal(groups[2].name, "trans · 2-F");
  assert.deepEqual(Array.from(groups[0].entries, (entry) => entry.molecule.id), ["a", "b", "e", "d"]);
  assert.equal(groups[0].entries[1].label, "Minimum · 1");
  assert.equal(groups[0].entries[2].label, "Minimum · 2");
  assert.equal(groups[0].entries[3].label, "Übergangszustand");
  assert.equal(context.structureGroups(molecules, "trans")[0].entries[0].molecule.id, "c");
  assert.equal(context.structureGroups(molecules, "C12H9FN2")[0].entries[0].molecule.id, "f");
  assert.equal(context.structureGroups(molecules, "Minimum · 2")[0].entries[0].molecule.id, "e");
  assert.equal(context.structureGroups(molecules.filter((m) => m.id !== "a"))[0].entries.length, 3);

});

function selectionLab(molecules) {
  const elements = new Map();
  const context = vm.createContext({
    state: { molecules, selected: null, resultSelection: null, step: "build" },
    TITLES: { build: [], optimize: [], spectrum: [] },
    document: { querySelectorAll: () => [] },
    stopAnimation() {},
    renderState() {},
    $: (id) => {
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    },
    api: async () => ({ molecules: context.state.molecules }),
  });
  loadSelectionFunctions(context);
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  vm.runInContext(
    app.slice(
      app.indexOf("function navigate("),
      app.indexOf("let energyChart ="),
    ),
    context,
  );
  return context;
}

const selectionMolecules = () => [
  { id: "start", kind: "initial", base_name: "trans-Azobenzol" },
  { id: "other", kind: "initial", base_name: "cis-Azobenzol" },
  {
    id: "min",
    kind: "minimum",
    parent_id: "start",
    base_name: "trans-Azobenzol",
  },
  { id: "ts", kind: "ts", parent_id: "min", base_name: "trans-Azobenzol" },
];

test("build offers only starting structures and a round trip restores the selected result", () => {
  const lab = selectionLab(selectionMolecules());
  lab.selectMolecule("ts");
  assert.equal(lab.state.selected, "start");
  assert.deepEqual(
    Array.from(lab.selectableMolecules(), (m) => m.id),
    ["start", "other"],
  );
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "ts");
  assert.equal(lab.selectableMolecules().length, 4);
  lab.navigate("build");
  assert.equal(lab.state.selected, "start");
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "ts");
  lab.navigate("spectrum");
  lab.selectMolecule("min");
  lab.navigate("build");
  assert.equal(lab.state.selected, "start");
  lab.navigate("spectrum");
  assert.equal(lab.state.selected, "min");
  lab.navigate("build");
  lab.selectMolecule("other");
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "other");
});

test("refresh and background results preserve the build filter and remember the latest result", async () => {
  const lab = selectionLab(selectionMolecules());
  await lab.refresh();
  assert.equal(lab.state.selected, "start");
  await lab.refresh();
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "ts");
  lab.navigate("build");
  lab.state.molecules.push({
    id: "new-ts",
    kind: "ts",
    parent_id: "min",
    base_name: "trans-Azobenzol",
  });
  await lab.refresh("new-ts");
  assert.equal(lab.state.selected, "start");
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "new-ts");
  lab.navigate("build");
  lab.state.molecules.push({
    id: "new-start",
    kind: "initial",
    base_name: "trans-2-Me-Azobenzol",
  });
  await lab.refresh("new-start");
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "new-start");
});

test("deleted parents and results never expose a result as a starting structure", async () => {
  const lab = selectionLab(selectionMolecules().filter((m) => m.id !== "min"));
  lab.selectMolecule("ts");
  assert.equal(lab.state.selected, "start");
  lab.state.molecules = lab.state.molecules.filter((m) => m.id !== "ts");
  await lab.refresh();
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "start");
  lab.navigate("build");
  lab.state.molecules = [
    {
      id: "orphan",
      kind: "minimum",
      parent_id: "deleted",
      base_name: "trans-Azobenzol",
    },
  ];
  await lab.refresh("orphan");
  assert.equal(lab.state.selected, null);
  assert.equal(lab.selectableMolecules().length, 0);
  lab.navigate("optimize");
  assert.equal(lab.state.selected, "orphan");
});

test("clear structures confirms the full scope and resets selection only after successful deletion", async () => {
  const elements = new Map();
  let approved = false,
    fail = false;
  const calls = [];
  const context = vm.createContext({
    state: {
      busy: false,
      molecules: [{ id: "start" }, { id: "ts" }],
      selected: "start",
      resultSelection: "ts",
      step: "build",
      tracking: {},
      live: {},
    },
    window: {
      confirm: (message) => {
        assert.match(message, /Minima.*Übergangszustände.*Spektren/);
        return approved;
      },
    },
    handle: (fn) => fn,
    api: async (path, options) => {
      calls.push([path, options.method]);
      if (fail) throw Error("busy elsewhere");
    },
    stopAnimation() {},
    refresh: async () => {
      context.state.molecules = [];
    },
    updateControls() {},
    toast() {},
    $: (id) => {
      if (!elements.has(id)) elements.set(id, { close() {}, focus() {} });
      return elements.get(id);
    },
  });
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const start = app.indexOf('$("clear-structures").onclick');
  vm.runInContext(
    app.slice(start, app.indexOf("\ndocument\n", start)),
    context,
  );
  const clear = elements.get("clear-structures").onclick;
  await clear();
  assert.equal(calls.length, 0);
  assert.equal(context.state.selected, "start");
  approved = true;
  context.state.busy = true;
  await clear();
  assert.equal(calls.length, 0);
  context.state.busy = false;
  fail = true;
  await assert.rejects(clear(), /busy elsewhere/);
  assert.equal(context.state.resultSelection, "ts");
  fail = false;
  await clear();
  assert.deepEqual(calls.at(-1), ["molecules", "DELETE"]);
  for (const field of [
    "selected",
    "resultSelection",
    "live",
    "tracking",
    "previewIndex",
  ])
    assert.equal(context.state[field], null);
  assert.equal(context.state.molecules.length, 0);
});

test("completion keeps the live view until the result is loaded, then switches atomically", async () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  let resolveSession;
  const elements = new Map();
  const source = { id: "source" };
  const result = { id: "result" };
  const live = { source_id: "source", step: 3 };
  const rendered = [];
  const context = vm.createContext({
    state: { molecules: [source], selected: "source", step: "optimize", busy: true, live },
    api: () => new Promise((resolve) => { resolveSession = resolve; }),
    selectMolecule: (id) => { context.state.selected = id; },
    renderState: () => rendered.push({
      selected: context.state.selected,
      busy: context.state.busy,
      live: context.state.live,
    }),
    $: (id) => {
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    },
  });
  vm.runInContext(app.slice(app.indexOf("async function refresh("), app.indexOf("let energyChart = null;")), context);
  const refresh = context.refresh("result", true);
  assert.equal(context.state.busy, true);
  assert.equal(context.state.live, live);
  assert.equal(context.state.selected, "source");
  assert.equal(rendered.length, 0);
  resolveSession({ molecules: [source, result] });
  await refresh;
  assert.deepEqual(rendered, [{ selected: "result", busy: false, live: null }]);
});


test("minimum playback uses its optimization history without a mode toggle", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const records = [record(0), record(1), record(2)];
  let molecule = { id: "minimum", kind: "minimum" };
  const context = vm.createContext({
    OptimizationProgress: progress,
    current: () => molecule,
    energyRecords: () => records,
  });
  vm.runInContext(app.slice(app.indexOf("function playbackData()"), app.indexOf("function renderPlaybackControls()")), context);
  const data = context.playbackData();
  assert.equal(data.kind, "optimization");
  assert.deepEqual(Array.from(data.frames), records.map((p) => p.positions));
  molecule = { id: "ts", ts_search: {}, frames: [[0, 0, 0]] };
  assert.equal(context.playbackData().frames.length, 0);
});

test("spectrum preserves bands and stick strengths with reciprocal wavelength ticks", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  let chart;
  const selection = {};
  const context = vm.createContext({
    spectrumChart: null,
    HC: 1239.8419843320026,
    fmt: (value) => String(Math.round(value)),
    plotStyle: { text: "#586b80", font: { size: 16 }, titleFont: { size: 17 } },
    $: () => selection,
    Chart: class {
      constructor(_, config) { Object.assign(this, config); chart = this; }
      update() {}
    },
  });
  vm.runInContext(app.slice(app.indexOf("function renderSpectrumChart("), app.indexOf("function collectProgress(")), context);
  context.renderSpectrumChart({ energy_ev: [1.5, 3, 5.5], absorption: [0, 1, 0.2],
    excitations_ev: [1, 3, 5, 6], oscillator_strengths: [2, 0.7, 0.1, 3] });
  assert.deepEqual(Array.from(chart.data.datasets[0].data, (p) => p.y), [0, 1, 0.2]);
  assert.deepEqual(Array.from(chart.data.datasets[1].data, (p) => p.y), [0, 0.7, null, 0, 0.1, null]);
  assert.equal(chart.options.scales.x.min, 1.5);
  assert.equal(chart.options.scales.wavelength.max, 5.5);
  const axis = { min: 1.5, max: 5.5 };
  chart.options.scales.wavelength.afterBuildTicks(axis);
  assert.deepEqual(Array.from(axis.ticks, (t) => chart.options.scales.wavelength.ticks.callback(t.value)),
    ["800", "600", "500", "400", "300", "250"]);
  assert.equal(chart.options.scales.y.title.font.size, 17);
  chart.chartArea = { left: 0, right: 400, top: 0, bottom: 200 };
  chart.scales = { x: { min: 1.5, max: 5.5, getPixelForValue: (x) => (x - 1.5) * 100 } };
  chart.options.onClick({ x: 153, y: 100 }, [], chart);
  assert.equal(chart.data.datasets[2].data[1].x, 3);
  assert.equal(chart.data.datasets[2].data[1].y, 0.7);
  assert.match(selection.textContent, /Übergang 2/);
  chart.options.onClick({ x: 250, y: 100 }, [], chart); // Empty space does not select a band.
  assert.equal(chart.data.datasets[2].data[1].x, 3);
  chart.options.onClick({ x: 350, y: -1 }, [], chart); // Axis labels are not clickable lines.
  assert.equal(chart.data.datasets[2].data[1].x, 3);
  chart.options.onClick({ x: 350, y: 100 }, [], chart);
  assert.equal(chart.data.datasets[2].data[1].x, 5);
  assert.match(selection.textContent, /Übergang 3/);
});

test("spectrum notes rotate without inventing stage changes", () => {
  const spectrum = globalThis.SpectrumProgress;
  const first = spectrum.describe("excited_states", 0);
  const later = spectrum.describe("excited_states", 12);
  assert.equal(first.title, later.title);
  assert.notEqual(first.detail, later.detail);
  assert.equal(spectrum.describe("excited_states", 36).detail, first.detail);
  assert.match(spectrum.describe("unknown", 0).title, /wird berechnet/);
  assert.match(spectrum.describe("expanded_output", 0).detail, /erneut/);
});

test("spectrum stage descriptions only appear for a running spectrum job", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const elements = new Map();
  const context = vm.createContext({
    state: { step: "spectrum", busy: true },
    SpectrumProgress: globalThis.SpectrumProgress,
    JOBS: { uvvis: "UV/Vis-Spektrum wird berechnet", minimum: "Minimum wird gesucht" },
    fmt: String,
    renderEnergyHistory() {},
    $: (id) => {
      if (!elements.has(id)) elements.set(id, { classList: { toggle() {} } });
      return elements.get(id);
    },
  });
  vm.runInContext(app.slice(app.indexOf("function displayJob("), app.indexOf("async function monitor(")), context);
  const job = { kind: "uvvis", status: "running", elapsed: 24,
    spectrum_progress: { phase: "excited_states" } };
  context.displayJob(job);
  assert.equal(elements.get("job-detail").hidden, false);
  assert.equal(elements.get("job-title").textContent, "Energien angeregter Zustände berechnen");
  for (const status of ["queued", "failed", "cancelled", "timeout", "complete"]) {
    context.displayJob({ ...job, status });
    assert.equal(elements.get("job-detail").hidden, true);
    assert.notEqual(elements.get("job-title").textContent, "Energien angeregter Zustände berechnen");
  }
  context.displayJob({ ...job, kind: "minimum" });
  assert.equal(elements.get("job-detail").hidden, true);
});

test("picker groups by starting configuration and substitution without redundant origin text", () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const element = () => ({
    children: [], attributes: {}, classList: { toggle() {} }, textContent: "", value: "",
    append(...children) { this.children.push(...children); },
    replaceChildren() { this.children = []; },
    setAttribute(name, value) { this.attributes[name] = value; },
  });
  const elements = new Map();
  const molecules = [
    { id: "start", base_name: "trans-4-OMe-Azobenzol", kind: "initial", formula: "C13H12N2O" },
    { id: "min", base_name: "trans-4-OMe-Azobenzol", kind: "minimum", formula: "C13H12N2O" },
    { id: "ts", base_name: "trans-4-OMe-Azobenzol", kind: "ts", formula: "C13H12N2O" },
    { id: "failed", base_name: "cis-4-OMe-Azobenzol", kind: "unconverged", ts_search: {}, formula: "C13H12N2O" },
  ];
  const context = vm.createContext({
    state: { selected: "min", busy: false },
    KIND: { initial: "Startstruktur", minimum: "Minimum", ts: "Übergangszustand", unconverged: "Optimierung nicht abgeschlossen" },
    selectableMolecules: () => molecules,
    document: { createElement: element },
    handle: (fn) => fn,
    $: (id) => {
      if (!elements.has(id)) elements.set(id, element());
      return elements.get(id);
    },
  });
  vm.runInContext(app.slice(app.indexOf("function substituentLabel("), app.indexOf("for (let r =")), context);
  vm.runInContext(app.slice(app.indexOf("function structureIdentity("), app.indexOf('$("molecule-select").onclick')), context);
  context.renderStructureOptions();
  const groups = elements.get("structure-options").children;
  assert.equal(groups.length, 2);
  assert.equal(groups[0].children[0].textContent, "trans · 4-OMe");
  assert.equal(groups[1].children[0].textContent, "cis · 4-OMe");
  const buttons = groups[0].children.slice(2).map((row) => row.children[0]);
  const minimum = buttons.find((button) => button.attributes["aria-current"] === "true");
  assert.equal(minimum.children[0].textContent, "Minimum");
  assert.equal(minimum.children[0].children[0].textContent, "✓");
  const ts = buttons.find((button) => button.children[0].textContent === "Übergangszustand");
  assert.equal(ts.children[0].children.length, 0);
  assert.equal(ts.children.length, 1);
  assert.equal(ts.attributes["aria-label"], "trans · 4-OMe · Übergangszustand");
  const failed = groups[1].children[2].children[0];
  assert.equal(failed.children[0].textContent, "Optimierung nicht abgeschlossen");
  for (const button of [...buttons, failed]) {
    assert.doesNotMatch(button.attributes["aria-label"], /Azobenzol|Ausgangsminimum/);
  }
  elements.get("structure-search").value = "cis · 4-OMe";
  context.renderStructureOptions();
  assert.equal(elements.get("structure-options").children.length, 1);
  assert.equal(elements.get("structure-options").children[0].children.length, 3);
});

test("Logout uses the public Hub URL and disappears in local mode", async () => {
  const app = fs.readFileSync("src/achprak/web/static/app.js", "utf8");
  const elements = new Map();
  let session = {
    molecules: [], user: "student",
    hub: { logout: "/jhub/hub/logout" },
  };
  const context = vm.createContext({
    state: { molecules: [], step: "build" },
    api: async () => session,
    selectMolecule: () => {},
    renderState: () => {},
    $: (id) => {
      if (!elements.has(id)) elements.set(id, {});
      return elements.get(id);
    },
  });
  vm.runInContext(app.slice(app.indexOf("async function refresh("), app.indexOf("let energyChart = null;")), context);
  await context.refresh();
  assert.equal(elements.get("hub-logout").href, "/jhub/hub/logout");
  assert.equal(elements.get("hub-logout").hidden, false);
  assert.equal(elements.get("hub-logout").title, "Angemeldet als student");
  assert.equal(elements.get("hub-logout").ariaLabel, "Abmelden (student)");
  session = { molecules: [], user: null, hub: null };
  await context.refresh();
  assert.equal(elements.get("hub-logout").hidden, true);
  assert.equal(elements.get("hub-logout").href, "");
  assert.equal(elements.get("hub-logout").title, "");
});
