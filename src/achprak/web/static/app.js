"use strict";
const $ = (id) => document.getElementById(id);
const SUBS = ["H", "Me", "NMe2", "CF3", "OMe", "F", "SO2CF3"];
for (let r = 0; r < 2; r++) {
  const field = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = r ? "Ring 2′–6′" : "Ring 2–6";
  field.append(legend);
  for (let c = 0; c < 5; c++) {
    const row = document.createElement("div");
    row.className = "ring-row";
    const label = document.createElement("label");
    label.htmlFor = `sub-${r * 5 + c}`;
    label.textContent = `${c + 2}${r ? "′" : ""}`;
    const select = document.createElement("select");
    select.id = label.htmlFor;
    select.setAttribute("aria-label", `Substituent an C${label.textContent}`);
    SUBS.forEach((s) => select.add(new Option(s, s)));
    row.append(label, select);
    field.append(row);
  }
  $("rings").append(field);
}
const state = {
  molecules: [],
  selected: null,
  step: "build",
  mode: "3d",
  busy: false,
  job: null,
  live: null,
  tracking: null,
  replaying: false,
  playbackMode: "optimization",
  playbackMolecule: null,
  previewIndex: null,
};
let stage = null,
  component = null,
  renderVersion = 0,
  animation = null;
const TITLES = {
  build: [
    "Ein Molekül, viele Möglichkeiten.",
    "Wählen Sie Konfiguration und Substituenten für Ihre Startstruktur.",
  ],
  properties: [
    "Die räumliche Struktur verstehen.",
    "Vergleichen Sie Energie, Verdrehung und Ringabstand Ihrer Moleküle.",
  ],
  optimize: [
    "Der stabilen Geometrie auf der Spur.",
    "Finden Sie Minimumsstrukturen und den Übergangszustand der Isomerisierung.",
  ],
  spectrum: [
    "Sichtbar machen, was Licht bewirkt.",
    "Untersuchen Sie die Absorption und den Einfluss Ihrer Substituenten.",
  ],
};
const JOBS = {
  template: "Struktur wird erstellt",
  properties: "Eigenschaften werden berechnet",
  minimum: "Minimum wird optimiert",
  ts: "Übergangszustand wird gesucht",
  uvvis: "UV/Vis-Spektrum wird berechnet",
};
const KIND = {
  initial: "Startstruktur",
  minimum: "Optimiertes Minimum",
  ts: "Übergangszustand",
  unconverged: "Nicht konvergiert",
};
const HC = 1239.8419843320026,
  EV_KJ = 96.48533212331002;
const current = () => state.molecules.find((m) => m.id === state.selected);
const fmt = (value, digits = 2) =>
  Number(value).toLocaleString("de-DE", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
function error(message) {
  $("alert").textContent = message;
  $("alert").hidden = !message;
}
let toastTimer;
function toast(message) {
  $("toast").textContent = message;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => ($("toast").hidden = true), 3000);
}
async function api(path, options = {}) {
  const response = await fetch(`api/${path}`, {
    credentials: "same-origin",
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-AChPrak-Request": "1",
      ...options.headers,
    },
  });
  const data = await response.json();
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Bitte überprüfen Sie Ihre Eingaben.",
    );
  return data;
}
function download(data, filename, type) {
  const blob = data instanceof Blob ? data : new Blob([data], { type });
  const url = URL.createObjectURL(blob),
    link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function filename(ext) {
  return (
    (current()?.name || "photoschalter")
      .replace(/[^\p{L}\p{N}._-]+/gu, "-")
      .slice(0, 100) +
    "." +
    ext
  );
}
function svgURL(svg) {
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}
function stopAnimation() {
  clearInterval(animation);
  animation = null;
  $("play").textContent = "Abspielen";
  $("play").setAttribute("aria-label", "Verlauf einmal abspielen");
}
function playbackData() {
  return OptimizationProgress.playback(
    current(),
    energyRecords(),
    state.playbackMode,
  );
}
function renderPlaybackControls() {
  const data = playbackData();
  $("trajectory").hidden =
    state.busy || state.mode !== "3d" || !component || !data.frames.length;
  $("playback-mode").hidden =
    !current()?.ts_search?.path?.length &&
    (current()?.trajectory_kind !== "vibration" || !energyRecords().length);
  $("playback-mode").querySelector('[value="path"]').hidden =
    !current()?.ts_search?.path?.length;
  $("playback-mode").querySelector('[value="vibration"]').hidden =
    current()?.trajectory_kind !== "vibration";
  $("playback-mode").value = data.kind;
  $("trajectory-label").textContent =
    data.kind === "path"
      ? "Pfadbild ansehen"
      : data.kind === "vibration"
        ? "Bild ansehen"
        : "Schritt ansehen";
  $("frame").max = String(Math.max(0, data.frames.length - 1));
  $("frame").value = String(
    state.previewIndex ?? Math.max(0, data.frames.length - 1),
  );
  $("frame-label").textContent =
    state.previewIndex === null
      ? "Ergebnis"
      : data.kind === "vibration"
        ? `${state.previewIndex + 1} / ${data.frames.length}`
        : `${data.records[state.previewIndex]?.step ?? state.previewIndex} / ${data.records.at(-1)?.step ?? data.frames.length - 1}`;
}
function showFrame(index) {
  const data = playbackData();
  if (state.busy || !component || !data.frames[index]) return;
  state.previewIndex = index;
  state.live = {
    ...data.records[index],
    source_id: state.selected,
    positions: data.frames[index],
    replay: true,
    phase:
      data.kind === "vibration"
        ? "vibration-preview"
        : data.kind === "path"
          ? "path"
          : data.records[index]?.phase || "optimization",
  };
  applyLiveGeometry();
  renderEnergyHistory(data.records[index]?.step);
  renderPlaybackControls();
}
function showResult() {
  stopAnimation();
  state.previewIndex = null;
  state.live = null;
  renderState();
}
function ensureStage() {
  if (!stage) {
    stage = new NGL.Stage("viewport", {
      backgroundColor: "#fafcff",
      quality: "medium",
    });
    new ResizeObserver(() => stage.handleResize()).observe($("viewport"));
  }
  return stage;
}
async function renderMolecule() {
  const version = ++renderVersion,
    m = current();
  stopAnimation();
  $("trajectory").hidden = true;
  if (stage) stage.removeAllComponents();
  component = null;
  $("viewer-empty").hidden = !!m;
  $("viewer-hint").hidden = !m || state.mode !== "3d";
  if (!m) {
    $("structure-image").removeAttribute("src");
    return;
  }
  $("structure-image").src = svgURL(m.svg);
  if (state.mode !== "3d" || state.step === "spectrum") return;
  try {
    const viewer = ensureStage();
    const loaded = await viewer.loadFile(
      new Blob([m.sdf], { type: "text/plain" }),
      { ext: "sdf" },
    );
    if (version !== renderVersion) {
      viewer.removeComponent(loaded);
      return;
    }
    component = loaded;
    component.addRepresentation("ball+stick", {
      aspectRatio: 1.8,
      bondScale: 0.35,
      multipleBond: "symmetric",
    });
    component.autoView(0);
    viewer.viewerControls.zoom(0.35);
    viewer.handleResize();
    applyLiveGeometry();
    renderPlaybackControls();
  } catch (exc) {
    error(
      "Das 3D-Modell konnte nicht geladen werden. Prüfen Sie, ob WebGL im Browser aktiviert ist. Die Strukturformel ist weiterhin verfügbar.",
    );
    state.mode = "2d";
    updateMode();
    console.error(exc);
  }
}
function updateMode() {
  $("viewport").hidden = state.mode !== "3d";
  $("structure-image").hidden = state.mode !== "2d" || !current();
  for (const mode of ["3d", "2d"]) {
    $("view-" + mode).classList.toggle("selected", state.mode === mode);
    $("view-" + mode).setAttribute("aria-pressed", String(state.mode === mode));
  }
  $("viewer-hint").hidden = !current() || state.mode !== "3d";
  $("center").disabled = !current() || state.mode !== "3d";
  $("properties-grid").hidden = !!state.live;
  renderPlaybackControls();
  if (state.mode !== "3d") {
    stopAnimation();
    $("trajectory").hidden = true;
  }
}
function updateControls() {
  const m = current();
  for (const id of ["calculate-properties", "optimize"])
    $(id).disabled = state.busy || !m;
  const tsSelected =
    document.querySelector("input[name=target]:checked").value === "ts";
  $("optimization-method").textContent = tsSelected
    ? "GFN1-xTB · CI-NEB · Sella"
    : "GFN1-xTB · Sella";
  $("ts-requirement").hidden = !tsSelected || m?.kind === "minimum";
  $("optimize").disabled =
    state.busy || !m || (tsSelected && m.kind !== "minimum");
  $("create").disabled = state.busy;
  $("delete-molecule").disabled = state.busy || !m;
  $("molecule-select").disabled = state.busy || !state.molecules.length;
  $("calculate-spectrum").disabled = state.busy || m?.kind !== "minimum";
  $("spectrum-requirement").textContent =
    m?.kind === "minimum"
      ? "Optimiertes Minimum ausgewählt. Die Struktur ist bereit für die Spektrenberechnung."
      : "Wählen Sie eine optimierte Minimumsstruktur aus Ihrer Liste oder optimieren Sie zuerst ein Molekül.";
  for (const id of ["xyz-download", "xyz-copy", "image-download"])
    $(id).disabled = !m || !!state.live;
  $("trajectory-download").disabled = !m?.frames?.length || !!state.live;
  updateMode();
}
function renderSpectrum() {
  const spec = current()?.spectrum;
  $("spectrum-empty").hidden = !!spec;
  $("spectrum-result").hidden = !spec;
  if (!spec) return;
  $("spectrum-image").src = svgURL(spec.svg);
  const peak = spec.absorption.indexOf(Math.max(...spec.absorption)),
    e = spec.energy_ev[peak];
  $("spectrum-caption").textContent =
    `Maximum im berechneten Bereich: ${fmt(e, 3)} eV · ${fmt(HC / e, 1)} nm. Gaußverbreiterung: σ = 0,3 eV.`;
  $("transitions").replaceChildren();
  spec.excitations_ev.forEach((e, i) => {
    const tr = document.createElement("tr");
    [
      i + 1,
      fmt(e, 4),
      fmt(HC / e, 1),
      fmt(spec.oscillator_strengths[i], 4),
    ].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value;
      tr.append(td);
    });
    $("transitions").append(tr);
  });
}
function renderState() {
  const m = current();
  if (state.playbackMolecule !== m?.id) {
    state.playbackMolecule = m?.id;
    state.playbackMode = m?.ts_search?.path?.length ? "path" : "optimization";
    state.previewIndex = null;
  }
  if (state.live && state.live.source_id !== m?.id) state.live = null;
  $("molecule-select").textContent = m?.name || "Noch keine Struktur";
  $("molecule-select").title = m?.name || "Struktur auswählen";
  $("structure-count").textContent = String(state.molecules.length);
  $("active-name").textContent = m?.name || "Ihre erste Struktur";
  $("active-meta").textContent = m
    ? `${m.formula} · ${m.atom_count} Atome`
    : "Wählen Sie Konfiguration und Substituenten für Ihre Startstruktur.";
  $("geometry-badge").hidden = !m;
  $("geometry-badge").textContent = m ? KIND[m.kind] : "";
  $("geometry-badge").classList.toggle("optimized", m?.kind === "minimum");
  $("xyz-output").value = m?.xyz || "";
  $("energy").textContent = m?.properties
    ? fmt(m.properties.energy_ev, 4)
    : "—";
  $("dihedral").textContent = m?.properties
    ? fmt(m.properties.dihedral_deg, 1)
    : "—";
  $("distance").textContent = m?.properties
    ? fmt(m.properties.ring_distance_pm, 1)
    : "—";
  const ts = m?.ts_search;
  const legacyTS = m?.kind === "ts" && !ts;
  const comparisonEndpoints = ts?.connectivity?.reference_minima
    ? "nachoptimierten Band-Endpunkten"
    : "Band-Endpunkten";
  $("ts-summary").hidden = !ts && !legacyTS;
  $("ts-summary").textContent = !ts
    ? legacyTS
      ? "Älteres TS-Ergebnis ohne vollständige Modenprüfung. Für die neue Prüfung eine TS-Suche vom Minimum starten."
      : ""
    : ts.validation?.verified &&
        (ts.method !== "ci_neb_then_sella" || ts.connectivity?.verified)
      ? `TS-Prüfung: eine imaginäre Mode (${fmt(ts.validation.imaginary_frequency_cm1, 1)} i cm⁻¹, alle Atome). ΔE‡ zum Ausgangsminimum: ${fmt(ts.barrier_ev, 3)} eV / ${fmt(ts.barrier_ev * EV_KJ, 1)} kJ/mol. Elektronische Energiebarriere entlang des untersuchten Pfads.${ts.connectivity?.verified ? (ts.connectivity.endpoint_conformers_match ? " Abwärtswege erreichen beide Endpunktminima innerhalb der Prüftoleranzen." : ` Abwärtswege erreichen cis- und trans-Minima. Der Konformervergleich mit den ${comparisonEndpoints} liegt außerhalb der Prüftoleranzen.`) : ""}`
      : `TS nicht bestätigt: ${ts.failure_reason || "Die Suche wurde nicht erfolgreich abgeschlossen."}`;
  updateControls();
  renderSpectrum();
  renderEnergyHistory(state.live?.step);
  renderMolecule();
}
function navigate(step) {
  if (!(step in TITLES)) throw new Error("Unbekannter Versuchsschritt.");
  state.step = step;
  document.querySelectorAll("[data-step]").forEach((button) => {
    button.classList.toggle("active", button.dataset.step === step);
    if (button.dataset.step === step)
      button.setAttribute("aria-current", "step");
    else button.removeAttribute("aria-current");
  });
  document
    .querySelectorAll("[data-panel]")
    .forEach((panel) => (panel.hidden = panel.dataset.panel !== step));
  $("step-title").textContent = TITLES[step][0];
  $("step-description").textContent = TITLES[step][1];
  $("molecular-panel").hidden = step === "spectrum";
  $("spectrum-panel").hidden = step !== "spectrum";
  stopAnimation();
  renderMolecule();
}
async function refresh(selected) {
  const data = await api("session");
  state.molecules = data.molecules.map((m) => {
    // Also correct names of results already held by the running server.
    if (m.parent_id && ["minimum", "ts"].includes(m.kind)) {
      const base =
        m.base_name ||
        m.name.replace(/(?: · (?:Minimum|Übergangszustand))+$/, "");
      return {
        ...m,
        base_name: base,
        name: `${base} · ${m.kind === "ts" ? "Übergangszustand" : "Minimum"}`,
      };
    }
    return m;
  });
  state.selected =
    selected ||
    (state.molecules.some((m) => m.id === state.selected)
      ? state.selected
      : state.molecules.at(-1)?.id) ||
    null;
  $("user-label").textContent = data.user || "";
  renderState();
  return data;
}
let energyChart = null;
function energyRecords() {
  if (
    state.tracking?.sourceId === state.selected &&
    (state.busy || state.tracking.status !== "complete")
  )
    return state.tracking.records;
  return OptimizationProgress.merge([], current()?.optimization_history || []);
}
function renderEnergyHistory(activeStep) {
  const records = energyRecords();
  $("energy-history").hidden = !records.length;
  if (!records.length) return;
  const first = records[0],
    last = records.at(-1);
  const active = records.find((p) => p.step === activeStep) || last;
  const savedPath = current()?.ts_search?.path;
  const path = state.busy
    ? records.findLast((p) => p.step <= active.step && p.neb_path)?.neb_path
    : state.playbackMode !== "optimization"
      ? savedPath
      : null;
  const pathActive = state.live?.phase === "path" ? state.live : null;
  const live =
    state.busy &&
    !state.replaying &&
    state.tracking?.sourceId === state.selected &&
    ["queued", "running"].includes(state.tracking?.status);
  $("energy-history-state").textContent = state.replaying
    ? "· Wiedergabe"
    : live
      ? "· Live"
      : "";
  $("energy-history-value").textContent =
    `${state.live?.phase === "vibration-preview" ? "Optimierung · " : ""}Schritt ${active.step} · ${fmt(active.energy_ev, 4)} eV`;
  $("energy-reference").textContent =
    `ΔE relativ zu Schritt ${first.step}: E₀ = ${fmt(first.energy_ev, 6)} eV. GFN1-xTB · akzeptierte Geometrien.` +
    (records.some((p) => p.restart)
      ? " Kurvenunterbrechung: neuer Anlauf vom Minimum mit näher am Sattel liegender Startschätzung."
      : "");
  $("energy-chart").setAttribute(
    "aria-label",
    `Energieverlauf, ${records.length} Schritte. Anfang ${fmt(first.energy_ev, 6)} eV, zuletzt ${fmt(last.energy_ev, 6)} eV.`,
  );
  if (!energyChart) {
    energyChart = new Chart($("energy-chart"), {
      type: "line",
      data: {
        datasets: [
          {
            label: "ΔE",
            data: [],
            borderColor: "#165de1",
            borderWidth: 2,
            pointRadius: 0,
            pointHitRadius: 12,
            tension: 0,
          },
          {
            label: "Gezeigte Geometrie",
            data: [],
            borderColor: "#c77825",
            backgroundColor: "#c77825",
            pointRadius: 4,
            showLine: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        parsing: false,
        interaction: { mode: "nearest", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) =>
                items[0].raw.phase === "path"
                  ? `Pfadbild ${items[0].raw.image + 1}`
                  : `${{ endpoint: "Endpunktminimum", path_seed: "Pfadvorbereitung", neb: "NEB", neb_climb: "CI-NEB", connectivity: "Verbindungsprüfung", complete: "Geprüfter Sattel", scan: "Torsionsscan", refinement: "Sattelpunktverfeinerung", vibrations: "Schwingungsprüfung" }[items[0].raw.phase] || "Optimierung"} · Schritt ${items[0].raw.x} · Anlauf ${items[0].raw.attempt || 1}`,
              label: (item) =>
                `E = ${fmt(item.raw.energy, 6)} eV · ΔE = ${fmt(item.raw.y, 6)} eV`,
            },
          },
        },
        scales: {
          x: {
            type: "linear",
            title: { display: true, text: "Suchschritt" },
            ticks: { precision: 0, maxTicksLimit: 7 },
            grid: { display: false },
          },
          y: {
            title: { display: true, text: "ΔE / eV" },
            ticks: { maxTicksLimit: 5 },
            grid: { color: "#e7edf5" },
          },
        },
      },
    });
  }
  const point = (p) => ({
    x: p.step,
    y: p.energy_ev - first.energy_ev,
    energy: p.energy_ev,
    phase: p.phase,
    attempt: p.attempt || 1,
  });
  energyChart.data.datasets[0].data =
    OptimizationProgress.energyPoints(records);
  energyChart.data.datasets[1].data =
    state.live?.phase === "vibration-preview" ? [] : [point(active)];
  energyChart.options.scales.x.title.text = path?.length
    ? "Reaktionspfad (normierte Weglänge)"
    : "Optimierungsschritt";
  energyChart.options.scales.x.ticks.precision = path?.length ? 2 : 0;
  if (path?.length) {
    const pathPoint = (p) => ({
      x: p.coordinate,
      y: p.energy_ev - path[0].energy_ev,
      energy: p.energy_ev,
      phase: "path",
      image: p.image,
    });
    energyChart.data.datasets[0].data = path.map(pathPoint);
    const selected =
      pathActive ||
      (state.busy && active.neb_path
        ? path.find((p) => p.image === active.neb_image)
        : null) ||
      (state.live?.phase !== "vibration-preview"
        ? path.reduce((a, b) => (a.energy_ev > b.energy_ev ? a : b))
        : null);
    energyChart.data.datasets[1].data = selected ? [pathPoint(selected)] : [];
    $("energy-reference").textContent =
      "ΔE relativ zum Ausgangsminimum. Verbindungspfad zwischen beiden Minima; keine Zeitachse oder Folge von Optimierungsschritten.";
    $("energy-history-value").textContent = pathActive
      ? `Pfadbild ${pathActive.image + 1} / ${path.length} · ${fmt(pathActive.energy_ev, 4)} eV`
      : `Reaktionsprofil · ${path.length} Bilder`;
    $("energy-chart").setAttribute(
      "aria-label",
      `Energieprofil des Reaktionspfads mit ${path.length} Bildern`,
    );
  }
  energyChart.update("none");
}
function collectProgress(job) {
  if (!["minimum", "ts"].includes(job.kind)) return;
  const parsed = OptimizationProgress.parse(job.log || "");
  if (state.tracking?.jobId !== job.id)
    state.tracking = {
      jobId: job.id,
      records: [],
      sourceId: null,
      visibleSince: null,
      visibleSteps: new Set(),
    };
  const track = state.tracking;
  track.status = job.status;
  track.records = OptimizationProgress.merge(track.records, [
    ...parsed.records,
    ...(job.result?.molecule?.optimization_history || []),
  ]);
  track.sourceId = track.records[0]?.source_id;
  return track.records.at(-1);
}
async function replayShortRun() {
  const track = state.tracking;
  if (
    !track ||
    !OptimizationProgress.shouldReplay(
      track.records,
      track.visibleSince,
      performance.now(),
      track.visibleSteps?.size,
    )
  )
    return;
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  state.replaying = true;
  $("skip-replay").hidden = false;
  $("job-title").textContent =
    "Berechnung abgeschlossen · Verlauf wird wiedergegeben";
  const delay = Math.min(180, 3000 / track.records.length);
  try {
    for (const progress of track.records) {
      if (!state.replaying) break;
      state.live = { ...progress, replay: true };
      applyLiveGeometry();
      renderEnergyHistory(progress.step);
      $("job-time").textContent =
        `Wiedergabe · Schritt ${progress.step} · E = ${fmt(progress.energy_ev, 4)} eV`;
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  } finally {
    state.replaying = false;
    $("skip-replay").hidden = true;
  }
}
function applyLiveGeometry() {
  const progress = state.live;
  if (!progress || progress.source_id !== current()?.id) return;
  if (state.busy) stopAnimation();
  renderPlaybackControls();
  $("properties-grid").hidden = true;
  for (const id of [
    "xyz-download",
    "xyz-copy",
    "image-download",
    "trajectory-download",
  ])
    $(id).disabled = true;
  const in3D = state.mode === "3d";
  $("geometry-badge").textContent = in3D
    ? Number.isInteger(progress.neb_image)
      ? `${progress.replay ? "Wiedergabe" : "Live"} · NEB-Bild ${progress.neb_image + 1}`
      : progress.phase === "vibration-preview"
        ? "Wiedergabe · TS-Schwingung"
        : progress.replay
          ? "Wiedergabe · Zwischengeometrie"
          : "Live · Zwischengeometrie"
    : "Ausgangsstruktur · 2D";
  $("geometry-badge").classList.remove("optimized");
  if (
    component &&
    in3D &&
    progress.positions.length === component.structure.atomCount * 3
  ) {
    component.structure.updatePosition(new Float32Array(progress.positions));
    component.updateRepresentations({ position: true });
  }
}
function displayJob(job) {
  $("job-status").hidden = false;
  $("job-status").classList.toggle(
    "running",
    ["queued", "running"].includes(job.status),
  );
  const terminal = {
    complete: "Berechnung abgeschlossen",
    failed: "Berechnung fehlgeschlagen",
    cancelled: "Berechnung abgebrochen",
    timeout: "Zeitlimit erreicht",
  };
  $("job-title").textContent = terminal[job.status] || JOBS[job.kind];
  $("job-time").textContent =
    job.status === "queued"
      ? "Wartet auf einen freien Rechenplatz …"
      : `${fmt(job.elapsed || 0, 0)} s`;
  $("cancel").hidden = !["queued", "running"].includes(job.status);
  if (job.log !== undefined) {
    const { output } = OptimizationProgress.parse(job.log);
    const progress = collectProgress(job);
    $("log").textContent = output || "Berechnung wird vorbereitet …";
    if (job.status === "running" && progress) {
      state.live = progress;
      if (
        state.selected !== progress.source_id &&
        state.molecules.some((m) => m.id === progress.source_id)
      ) {
        state.selected = progress.source_id;
        renderState();
      }
      applyLiveGeometry();
      if (component && state.mode === "3d" && state.step !== "spectrum") {
        state.tracking.visibleSince ??= performance.now();
        state.tracking.visibleSteps.add(progress.step);
      }
      $("job-time").textContent =
        `${fmt(job.elapsed || 0, 0)} s · Schritt ${progress.step} · E = ${fmt(progress.energy_ev, 4)} eV · Fmax = ${fmt(progress.fmax_ev_angstrom, 4)} eV/Å`;
      const phaseTitle = {
        endpoint: "TS-Suche · gegenüberliegendes Minimum optimieren",
        path_seed: "TS-Suche · Verbindungspfad vorbereiten",
        neb: "TS-Suche · Verbindungspfad entspannen",
        neb_climb: "TS-Suche · CI-NEB zum Sattelpunkt",
        connectivity: "TS-Prüfung · Abwärtswege zu beiden Minima",
        complete: "TS-Prüfung abgeschlossen",
        scan: "TS-Suche · geführter Torsionsscan",
        refinement: "TS-Suche · freie Sattelpunktverfeinerung",
        vibrations: "TS-Prüfung · alle Schwingungsmoden werden berechnet",
      }[progress.phase];
      if (phaseTitle)
        $("job-title").textContent =
          (progress.attempt > 1 ? `Anlauf ${progress.attempt} · ` : "") +
          phaseTitle;
    }
  }
  renderEnergyHistory(state.live?.step);
  $("log-state").textContent = job.status === "running" ? "· läuft" : "";
}
async function monitor(jobId) {
  state.busy = true;
  state.job = jobId;
  updateControls();
  try {
    while (true) {
      const job = await api(`jobs/${jobId}`);
      displayJob(job);
      if (!["queued", "running"].includes(job.status)) {
        if (job.status === "complete" && ["minimum", "ts"].includes(job.kind))
          await replayShortRun();
        state.live = null;
        state.busy = false;
        displayJob(job);
        await refresh(job.result?.molecule?.id);
        if (job.error) error(job.error);
        if (job.result?.molecule?.converged === false)
          error(
            job.result.molecule.ts_search?.failure_reason ||
              "Die Optimierung ist nicht konvergiert. Die letzte Geometrie wurde gespeichert; sie ist nicht für ein Spektrum freigegeben.",
          );
        return job;
      }
      await new Promise((resolve) => setTimeout(resolve, 400));
    }
  } finally {
    state.busy = false;
    state.job = null;
    if (state.live) {
      state.live = null;
      renderState();
    }
    updateControls();
    renderEnergyHistory();
  }
}
async function startJob(payload) {
  if (state.busy)
    throw new Error("Bitte warten Sie auf die laufende Berechnung.");
  error("");
  const wasPreviewing = state.live?.replay;
  state.live = null;
  state.previewIndex = null;
  stopAnimation();
  state.tracking = null;
  if (wasPreviewing) renderState();
  if (["minimum", "ts"].includes(payload.kind)) {
    state.mode = "3d";
    updateMode();
    navigate("optimize");
  }
  state.busy = true;
  updateControls();
  try {
    const job = await api("jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    displayJob(job);
    $("log").textContent = "Berechnung wird vorbereitet …";
    return await monitor(job.id);
  } finally {
    state.busy = false;
    updateControls();
  }
}
function handle(action) {
  return async (event) => {
    event?.preventDefault();
    try {
      await action(event);
    } catch (exc) {
      error(exc.message);
    }
  };
}
function builderPayload() {
  const configuration = document.querySelector(
    "input[name=configuration]:checked",
  ).value;
  const substituents = Array.from(
    { length: 10 },
    (_, i) => $("sub-" + i).value,
  );
  return { kind: "template", settings: { configuration, substituents } };
}
$("builder").addEventListener(
  "submit",
  handle(() => startJob(builderPayload())),
);
$("calculate-properties").onclick = handle(() =>
  startJob({ kind: "properties", molecule_id: state.selected }),
);
document.querySelectorAll("input[name=target]").forEach((radio) => {
  radio.onchange = updateControls;
});
$("optimize").onclick = handle(() =>
  startJob({
    kind: document.querySelector("input[name=target]:checked").value,
    molecule_id: state.selected,
  }),
);
$("calculate-spectrum").onclick = handle(() =>
  startJob({ kind: "uvvis", molecule_id: state.selected }),
);
$("skip-replay").onclick = () => {
  state.replaying = false;
};
$("playback-mode").onchange = () => {
  state.playbackMode = $("playback-mode").value;
  showResult();
};
$("cancel").onclick = handle(async () => {
  if (state.job) await api(`jobs/${state.job}`, { method: "DELETE" });
});
function renderStructureOptions() {
  const query = $("structure-search").value.trim().toLocaleLowerCase("de-DE");
  $("structure-options").replaceChildren();
  for (const m of state.molecules.filter((m) =>
    `${m.name} ${m.formula}`.toLocaleLowerCase("de-DE").includes(query),
  )) {
    const button = document.createElement("button");
    button.className = "structure-option";
    button.classList.toggle("selected", m.id === state.selected);
    if (m.id === state.selected) button.setAttribute("aria-current", "true");
    const name = document.createElement("strong");
    name.textContent = m.name;
    const detail = document.createElement("small");
    detail.textContent = `${m.formula} · ${KIND[m.kind]}`;
    button.append(name, detail);
    button.onclick = () => {
      if (state.busy) return;
      state.live = null;
      state.selected = m.id;
      error("");
      renderState();
      $("structure-picker").close();
    };
    $("structure-options").append(button);
  }
  if (!$("structure-options").children.length) {
    const message = document.createElement("p");
    message.textContent = "Keine passende Struktur gefunden.";
    $("structure-options").append(message);
  }
}
$("molecule-select").onclick = () => {
  $("structure-search").value = "";
  renderStructureOptions();
  $("structure-picker").showModal();
  $("structure-search").focus();
};
$("structure-search").oninput = renderStructureOptions;
$("delete-molecule").onclick = handle(async () => {
  if (!current()) return;
  await api(`molecules/${state.selected}`, { method: "DELETE" });
  await refresh();
});
document
  .querySelectorAll("[data-step]")
  .forEach((button) => (button.onclick = () => navigate(button.dataset.step)));
for (const mode of ["3d", "2d"])
  $("view-" + mode).onclick = () => {
    state.mode = mode;
    updateMode();
    renderMolecule();
  };
$("center").onclick = () => {
  if (component) {
    component.autoView(0);
    stage.viewerControls.zoom(0.35);
  }
};
$("frame").oninput = () => {
  stopAnimation();
  showFrame(Number($("frame").value));
};
$("play").onclick = () => {
  if (animation) {
    stopAnimation();
    return;
  }
  const count = playbackData().frames.length;
  if (state.busy || !component || !count) return;
  let index = state.previewIndex ?? 0;
  if (index >= count - 1) index = 0;
  showFrame(index);
  if (index >= count - 1) return;
  $("play").textContent = "Pause";
  $("play").setAttribute("aria-label", "Wiedergabe pausieren");
  animation = setInterval(() => {
    showFrame(++index);
    if (index >= count - 1) stopAnimation();
  }, 150);
};
$("xyz-download").onclick = () =>
  download(current().xyz, filename("xyz"), "chemical/x-xyz");
$("xyz-copy").onclick = handle(async () => {
  await navigator.clipboard.writeText(current().xyz);
  toast("Koordinaten kopiert");
});
$("trajectory-download").onclick = () => {
  const m = current(),
    symbols = m.xyz
      .trim()
      .split("\n")
      .slice(2)
      .map((line) => line.trim().split(/\s+/)[0]);
  const xyz = playbackData()
    .frames.map(
      (frame, n) =>
        `${symbols.length}\nFrame ${n + 1}\n` +
        symbols
          .map((s, i) => `${s} ${frame.slice(i * 3, i * 3 + 3).join(" ")}`)
          .join("\n") +
        "\n",
    )
    .join("");
  download(xyz, filename("trajectory.xyz"), "chemical/x-xyz");
};
async function svgToPNG(svg, name) {
  const img = new Image();
  img.src = svgURL(svg);
  await img.decode();
  const canvas = document.createElement("canvas");
  canvas.width = 1600;
  canvas.height = Math.round((1600 * img.naturalHeight) / img.naturalWidth);
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise((resolve) =>
    canvas.toBlob(resolve, "image/png"),
  );
  if (!blob) throw new Error("Bild konnte nicht gespeichert werden.");
  download(blob, name);
}
$("image-download").onclick = handle(async () => {
  if (state.mode === "2d") await svgToPNG(current().svg, filename("png"));
  else {
    stopAnimation();
    if (!stage) throw new Error("3D-Modell ist noch nicht bereit.");
    download(
      await stage.makeImage({ factor: 2, antialias: true, trim: false }),
      filename("png"),
    );
  }
});
$("spectrum-svg").onclick = () =>
  download(current().spectrum.svg, filename("spectrum.svg"), "image/svg+xml");
$("spectrum-png").onclick = handle(() =>
  svgToPNG(current().spectrum.svg, filename("spectrum.png")),
);
$("spectrum-csv").onclick = () => {
  const s = current().spectrum;
  download(
    "energy_eV,wavelength_nm,absorption_au\n" +
      s.energy_ev.map((e, i) => `${e},${HC / e},${s.absorption[i]}`).join("\n"),
    filename("spectrum.csv"),
    "text/csv",
  );
};
document
  .querySelectorAll("[data-close]")
  .forEach(
    (button) => (button.onclick = () => $(button.dataset.close).close()),
  );
function convert(source) {
  const value = Number($("convert-" + source).value);
  if (!Number.isFinite(value) || $("convert-" + source).value === "") {
    for (const key of ["ev", "kj", "nm"])
      if (key !== source) $("convert-" + key).value = "";
    return;
  }
  const ev =
    source === "ev"
      ? value
      : source === "kj"
        ? value / EV_KJ
        : value > 0
          ? HC / value
          : NaN;
  const values = { ev, kj: ev * EV_KJ, nm: ev > 0 ? HC / ev : NaN };
  for (const key in values)
    if (key !== source)
      $("convert-" + key).value = Number.isFinite(values[key])
        ? Number(values[key].toPrecision(9))
        : "";
}
for (const key of ["ev", "kj", "nm"])
  $("convert-" + key).oninput = () => convert(key);
convert("ev");
$("converter-open").onclick = () => $("converter").showModal();
async function guide(step) {
  if (!$("guide-content").children.length) {
    const response = await fetch("static/guide.html");
    if (!response.ok) throw new Error("Aufgaben konnten nicht geladen werden.");
    $("guide-content").innerHTML = await response.text(); // Trusted, bundled teaching material.
  }
  $("guide").showModal();
  if (step) {
    const section = $("guide-" + step);
    section.open = true;
    section.scrollIntoView({ block: "start" });
  } else $("guide").scrollTop = 0;
}
$("guide-open").onclick = handle(() => guide());
$("task-open").onclick = handle(() => guide(state.step));
async function boot() {
  try {
    const data = await refresh();
    const active = data.jobs.find((j) =>
      ["queued", "running"].includes(j.status),
    );
    if (active) await monitor(active.id);
    else if (data.jobs.length)
      displayJob(await api(`jobs/${data.jobs.at(-1).id}`));
  } catch (exc) {
    error(exc.message);
  }
}
boot();
// Optional browser-native agent interface; uses the same actions as the UI.
if (document.modelContext?.registerTool) {
  const lifecycle = new AbortController();
  window.addEventListener("pagehide", () => lifecycle.abort(), { once: true });
  const tools = [
    {
      name: "read_lab_state",
      description: "Read the current molecule and calculation status.",
      inputSchema: {
        type: "object",
        properties: {},
        additionalProperties: false,
      },
      annotations: { readOnlyHint: true },
      execute: async () => ({
        step: state.step,
        busy: state.busy,
        molecules: state.molecules.map(({ id, name, kind }) => ({
          id,
          name,
          kind,
        })),
        selected: state.selected,
      }),
    },
    {
      name: "create_azobenzene",
      description:
        "Create an azobenzene structure and select it in the laboratory. Waits for the calculation.",
      inputSchema: {
        type: "object",
        properties: {
          configuration: { type: "string", enum: ["cis", "trans"] },
          substituents: {
            type: "array",
            items: { type: "string", enum: SUBS },
            minItems: 10,
            maxItems: 10,
          },
        },
        required: ["configuration", "substituents"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false },
      execute: async (input) => {
        if (
          !input ||
          !["cis", "trans"].includes(input.configuration) ||
          !Array.isArray(input.substituents) ||
          input.substituents.length !== 10 ||
          input.substituents.some((s) => !SUBS.includes(s))
        )
          throw new Error("Ungültige Strukturparameter.");
        navigate("build");
        document.querySelector(
          `input[name=configuration][value=${input.configuration}]`,
        ).checked = true;
        input.substituents.forEach((s, i) => ($("sub-" + i).value = s));
        const job = await startJob(builderPayload());
        return {
          status: job.status,
          molecule_id: job.result?.molecule?.id,
          error: job.error,
        };
      },
    },
  ];
  for (const tool of tools)
    Promise.resolve(
      document.modelContext.registerTool(tool, { signal: lifecycle.signal }),
    ).catch(console.warn);
}
