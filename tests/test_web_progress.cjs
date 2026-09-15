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
          setAttribute() {},
          querySelector() {
            return {};
          },
        });
      return elements.get(id);
    },
    applyLiveGeometry: () => geometries.push(context.state.live.positions),
    renderEnergyHistory: (step) => energies.push(step),
    renderState: () => {},
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
      app.indexOf('$("frame").oninput'),
      app.indexOf('$("xyz-download").onclick'),
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
  assert.equal(context.state.previewIndex, 2);
  assert.equal(timers.size, 0);
  assert.equal(play.textContent, "Abspielen");
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
  elements.get("frame").value = "2";
  elements.get("frame").oninput();
  play.onclick(); // The same applies to a manually selected final frame.
  assert.equal(context.state.previewIndex, 0);
  play.onclick(); // Pause before testing intermediate-step resume.

  elements.get("frame").value = "1";
  elements.get("frame").oninput();
  play.onclick(); // Resume from the manually selected step.
  assert.equal(context.state.previewIndex, 1);
  tick();
  assert.equal(context.state.previewIndex, 2);
  assert.equal(timers.size, 0);

  elements.get("frame").value = "0";
  elements.get("frame").oninput();
  play.onclick();
  tick();
  elements.get("frame").value = "0";
  elements.get("frame").oninput(); // Scrubbing pauses ongoing playback.
  assert.equal(timers.size, 0);
  play.onclick();
  assert.equal(context.state.previewIndex, 0);
  tick();
  tick();
  assert.equal(timers.size, 0);
});

test("TS scan, refinement and all-atom validation keep one continuous energy history", () => {
  const records = [
    record(0, "scan"),
    record(1, "scan"),
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

test("retry history preserves both attempts without plotting a fictitious downhill connection", () => {
  const records = [
    { ...record(0, "scan"), energy_ev: -10, attempt: 1 },
    { ...record(1, "refinement"), energy_ev: -9, attempt: 1 },
    { ...record(2, "scan"), energy_ev: -10, attempt: 2, restart: true },
    { ...record(3, "refinement"), energy_ev: -8, attempt: 2 },
  ];
  const history = progress.merge(
    [],
    progress.parse(records.map(line).join("\n")).records,
  );
  assert.equal(history.length, 4);
  const points = progress.energyPoints(history);
  assert.deepEqual(
    points.map((p) => p.y),
    [0, 1, null, 0, 2],
  );
  assert.equal(points[3].attempt, 2);
  assert.deepEqual(
    progress.playback({}, history, "optimization").frames,
    records.map((p) => p.positions),
  );
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
    state: { selected: "m", busy: false, playbackMode: "path", live: null },
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
  assert.match(chart.options.scales.x.title.text, /Reaktionspfad/);
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
    state: {
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
      if (!elements.has(id)) elements.set(id, { classList: { remove() {} } });
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
  assert.equal(elements.get("geometry-badge").textContent, "Live · NEB-Bild 4");
  context.state.live.source_id = "another-molecule";
  context.applyLiveGeometry();
  assert.equal(positions.length, 2);
});
