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
function summarizeSubstituents() {
  const count = [...$("rings").querySelectorAll("select")].filter(
    (select) => select.value !== "H",
  ).length;
  $("substituent-count").textContent = count ? `${count} gewählt` : "keine";
}
$("rings").addEventListener("change", summarizeSubstituents);
const state = {
  molecules: [],
  selected: null,
  resultSelection: null,
  step: "build",
  mode: "2d",
  buildMode: "2d",
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
  renderedMolecule = null,
  loadingMolecule = null,
  animation = null;
const TITLES = {
  build: [
    "Struktur erstellen",
    "Wählen Sie cis oder trans. Substituenten können Sie bei Bedarf ergänzen.",
  ],
  optimize: [
    "Struktur optimieren",
    "Wählen Sie eine Struktur und das Ziel der Optimierung.",
  ],
  spectrum: [
    "UV/Vis-Spektrum berechnen",
    "Berechnen Sie, welches Licht Ihr optimiertes Molekül absorbiert.",
  ],
};
const JOBS = {
  template: "Struktur wird erstellt",
  minimum: "Minimum wird gesucht",
  ts: "Übergangszustand wird gesucht",
  uvvis: "UV/Vis-Spektrum wird berechnet",
};
const KIND = {
  initial: "Startstruktur",
  minimum: "Minimum",
  ts: "Übergangszustand",
  unconverged: "Optimierung nicht abgeschlossen",
};
const HC = 1239.8419843320026,
  EV_KJ = 96.48533212331002;
const current = () => state.molecules.find((m) => m.id === state.selected);
function selectableMolecules() {
  return state.step === "build"
    ? state.molecules.filter((m) => m.kind === "initial")
    : state.molecules;
}
function startingStructure(molecule) {
  const seen = new Set();
  let source = molecule;
  while (source && !seen.has(source.id)) {
    if (source.kind === "initial") return source;
    seen.add(source.id);
    source = state.molecules.find((m) => m.id === source.parent_id);
  }
  // A recalculated/deleted minimum can break a TS's parent chain.
  return state.molecules.find(
    (m) => m.kind === "initial" && m.base_name === molecule?.base_name,
  );
}
function selectMolecule(id, rememberResult = true) {
  const molecule = state.molecules.find((m) => m.id === id);
  if (rememberResult) state.resultSelection = molecule?.id || null;
  state.selected =
    (state.step === "build" ? startingStructure(molecule)?.id : molecule?.id) ||
    selectableMolecules().at(-1)?.id ||
    null;
}
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
  const unavailable =
    state.busy || state.mode !== "3d" || !component || !data.frames.length;
  $("trajectory").hidden = state.step !== "optimize" || !data.frames.length;
  $("play").hidden = state.step !== "optimize";
  $("play").disabled = unavailable;
  $("energy-chart").setAttribute("aria-disabled", String(unavailable));
  $("playback-mode").hidden =
    !current()?.ts_search?.path?.length &&
    current()?.trajectory_kind !== "vibration";
  $("plot-hint").hidden = unavailable;
  $("playback-mode").disabled =
    unavailable ||
    (!current()?.ts_search?.path?.length &&
      current()?.trajectory_kind !== "vibration");
  $("playback-mode").querySelector('[value="path"]').hidden =
    !current()?.ts_search?.path?.length;
  $("playback-mode").querySelector('[value="vibration"]').hidden =
    current()?.trajectory_kind !== "vibration";
  $("playback-mode").value = data.kind;
}
function showFrame(index) {
  const data = playbackData();
  if (state.busy || !component || !data.frames[index]) return;
  if (data.kind === "optimization" && index === data.frames.length - 1) {
    showResult();
    return;
  }
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
function restoreResultGeometry() {
  const positions = current()
    .xyz.trim()
    .split("\n")
    .slice(2)
    .flatMap((line) => line.trim().split(/\s+/).slice(1, 4).map(Number));
  component.structure.updatePosition(new Float32Array(positions));
  component.updateRepresentations({ position: true });
}
async function renderMolecule() {
  const m = current();
  $("viewer-empty").hidden = !!m;
  $("viewer-hint").hidden = !m || state.mode !== "3d";
  if (!m) {
    ++renderVersion;
    loadingMolecule = renderedMolecule = null;
    if (stage) stage.removeAllComponents();
    component = null;
    $("structure-image").removeAttribute("src");
    renderPlaybackControls();
    return;
  }
  const image = svgURL(m.svg);
  if ($("structure-image").getAttribute("src") !== image)
    $("structure-image").src = image;
  if (state.mode !== "3d" || state.step === "spectrum") return;
  if (component && renderedMolecule === m.id) {
    if (state.live && state.step === "optimize") applyLiveGeometry();
    else restoreResultGeometry();
    stage.handleResize();
    renderPlaybackControls();
    return;
  }
  if (loadingMolecule === m.id) return;
  const version = ++renderVersion;
  loadingMolecule = m.id;
  try {
    const viewer = ensureStage();
    const loaded = await viewer.loadFile(
      new Blob([m.sdf], { type: "text/plain" }),
      { ext: "sdf" },
    );
    if (version !== renderVersion || current()?.id !== m.id) {
      viewer.removeComponent(loaded);
      return;
    }
    // Keep the existing model visible until its replacement is ready.
    const previous = component;
    const preserveCamera =
      previous &&
      m.parent_id === renderedMolecule &&
      previous.structure.atomCount === loaded.structure.atomCount;
    component = loaded;
    renderedMolecule = m.id;
    component.addRepresentation("ball+stick", {
      aspectRatio: 1.8,
      bondScale: 0.35,
      multipleBond: "symmetric",
    });
    if (previous) viewer.removeComponent(previous);
    if (!preserveCamera) {
      component.autoView(0);
      viewer.viewerControls.zoom(0.35);
    }
    viewer.handleResize();
    if (state.live && state.step === "optimize") applyLiveGeometry();
    else restoreResultGeometry();
    renderPlaybackControls();
  } catch (exc) {
    if (version !== renderVersion) return;
    error(
      "Das 3D-Modell konnte nicht geladen werden. Prüfen Sie, ob WebGL im Browser aktiviert ist. Die Strukturformel finden Sie in Schritt 1.",
    );
    updateMode();
    console.error(exc);
  } finally {
    if (version === renderVersion) loadingMolecule = null;
  }
}
function updateMode() {
  state.mode = state.step === "build" ? state.buildMode || "2d" : "3d";
  $("build-view-toggle").hidden = state.step !== "build" || !current();
  for (const mode of ["2d", "3d"]) {
    $("build-view-" + mode).checked = (state.buildMode || "2d") === mode;
    $("build-view-" + mode).disabled = !current();
  }
  $("starting-geometry-note").hidden =
    state.step !== "build" || state.mode !== "3d" || !current();
  $("center").hidden = state.mode !== "3d";
  $("viewport").hidden = state.mode !== "3d";
  $("structure-image").hidden = state.mode !== "2d" || !current();
  $("viewer-hint").hidden = !current() || state.mode !== "3d";
  $("center").disabled = !current() || state.mode !== "3d";
  $("properties-grid").hidden = state.step !== "optimize" || !current();
  $("properties-grid").style.visibility = "visible";
  $("properties-context").hidden = state.step !== "optimize" || !state.live;
  $("properties-context").style.visibility = "visible";
  $("property-help").hidden = state.step !== "optimize" || !current();
  $("property-help").style.visibility = "visible";
  renderPlaybackControls();
  if (state.mode !== "3d") {
    stopAnimation();
  }
}
function updateControls() {
  const m = current();
  for (const id of ["optimize"]) $(id).disabled = state.busy || !m;
  const tsSelected =
    document.querySelector("input[name=target]:checked").value === "ts";
  $("optimization-method").textContent = tsSelected
    ? "GFN1-xTB · CI-NEB · Sella"
    : "GFN1-xTB · Sella";
  $("ts-requirement").hidden = !m || !tsSelected || m.kind === "minimum";
  $("optimize").disabled =
    state.busy ||
    !m ||
    (tsSelected && m.kind !== "minimum") ||
    (!tsSelected && m.kind === "minimum");
  $("optimize").textContent =
    !tsSelected && m?.kind === "minimum"
      ? "Minimum bereits gefunden"
      : "Optimierung starten";
  $("create").disabled = state.busy;
  $("molecule-select").disabled = state.busy || !selectableMolecules().length;
  $("clear-structures").disabled = state.busy || !state.molecules.length;
  $("calculate-spectrum").disabled = state.busy || m?.kind !== "minimum";
  $("spectrum-requirement").hidden = !m || m.kind === "minimum";
  $("spectrum-requirement").textContent =
    "Suchen Sie für diese Struktur zuerst ein Minimum.";
  $("calculate-spectrum").textContent = m?.spectrum
    ? "Spektrum neu berechnen"
    : "Spektrum berechnen";
  $("structure-library").hidden = !selectableMolecules().length;
  $("structure-picker-title").textContent =
    state.step === "build" ? "Startstruktur auswählen" : "Struktur auswählen";
  $("result-heading").hidden = !m;
  $("viewer-toolbar").hidden = !m;
  $("result-details").hidden = state.step === "build" || (!m && !state.job);
  $("calculation-log").hidden =
    state.step === "build" || !state.hasCalculationLog;
  $("coordinate-details").hidden = !m || state.step === "spectrum";
  $("trajectory-download").hidden = !m?.frames?.length;
  for (const id of ["xyz-download", "xyz-copy"])
    $(id).disabled = !m || (!!state.live && state.step === "optimize");
  $("image-download").disabled = !m;
  $("trajectory-download").disabled =
    !m?.frames?.length || (!!state.live && state.step === "optimize");
  updateMode();
}
function renderSpectrum() {
  const spec = current()?.spectrum;
  $("spectrum-empty").hidden = !!spec;
  $("spectrum-result").hidden = !spec;
  if (!spec) return;
  const spectrumImage = svgURL(spec.svg);
  if ($("spectrum-image").getAttribute("src") !== spectrumImage)
    $("spectrum-image").src = spectrumImage;
  const peak = spec.absorption.indexOf(Math.max(...spec.absorption)),
    e = spec.energy_ev[peak];
  $("spectrum-caption").textContent =
    `Maximum im berechneten Bereich: ${fmt(e, 3)} eV · ${fmt(HC / e, 1)} nm.`;
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
    stopAnimation();
    state.playbackMolecule = m?.id;
    state.playbackMode = m?.ts_search?.path?.length ? "path" : "optimization";
    state.previewIndex = null;
  }
  if (state.live && state.live.source_id !== m?.id) state.live = null;
  $("molecule-select").textContent = m
    ? `${m.base_name} · ${KIND[m.kind]}`
    : "Noch keine Struktur";
  $("molecule-select").title = m?.name || "Struktur auswählen";
  $("structure-count").textContent = String(
    structureGroups(selectableMolecules()).length,
  );
  $("active-name").textContent = m?.name || "Ihre erste Struktur";
  $("active-meta").textContent = m
    ? `${m.formula} · ${m.atom_count} Atome`
    : "Wählen Sie cis oder trans. Substituenten können Sie bei Bedarf ergänzen.";
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
  $("properties-context").textContent = !m
    ? ""
    : m.kind === "initial"
      ? "Werte der noch nicht optimierten Startstruktur"
      : m.kind === "unconverged"
        ? "Werte des letzten Rechenschritts – Optimierung nicht abgeschlossen"
        : "Werte der berechneten Ergebnisstruktur";
  const ts = m?.ts_search;
  $("ts-summary").hidden = state.step !== "optimize" || !ts;
  $("ts-summary").textContent = !ts
    ? ""
    : m.converged
      ? `Energiebarriere: ${fmt(ts.barrier_ev * EV_KJ, 1)} kJ/mol (${fmt(ts.barrier_ev, 3)} eV) gegenüber dem Ausgangsminimum.`
      : "Übergangszustand noch nicht bestätigt.";
  $("ts-details").hidden = state.step !== "optimize" || !ts;
  $("ts-check-result").textContent = !ts
    ? ""
    : ts.connectivity?.verified
      ? `Beide Seiten führen zu cis und trans.${ts.connectivity.endpoint_conformers_match ? "" : " Die genaue räumliche Anordnung weicht von den nachoptimierten Vergleichsstrukturen ab."} Die Barriere gilt für diesen Weg; Temperatureffekte sind nicht berücksichtigt.`
      : "Die Prüfung ist nicht abgeschlossen. Besprechen Sie das Ergebnis mit Ihrer Betreuung.";
  $("ts-check-technical").textContent = !ts
    ? ""
    : [
        ts.validation
          ? `Imaginäre Frequenzen mit einem Betrag über 20 cm⁻¹: ${ts.validation.imaginary_count}.`
          : "Schwingungsprüfung noch nicht abgeschlossen.",
        ts.validation?.imaginary_frequency_cm1
          ? `Betrag der imaginären Frequenz: ${fmt(ts.validation.imaginary_frequency_cm1, 1)} cm⁻¹.`
          : "",
        ts.failure_reason || "",
      ]
        .filter(Boolean)
        .join(" ");
  updateControls();
  renderSpectrum();
  renderEnergyHistory(state.live?.step);
  renderMolecule();
}
function navigate(step) {
  if (!(step in TITLES)) throw new Error("Unbekannter Versuchsschritt.");
  if (state.step === step) return;
  if (state.step !== "build") state.resultSelection = state.selected;
  const selection =
    state.step === "build" &&
    state.molecules.some((m) => m.id === state.resultSelection)
      ? state.resultSelection
      : state.selected;
  state.step = step;
  selectMolecule(selection, step !== "build");
  if (step === "optimize") state.mode = "3d";
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
  state.live = null;
  state.previewIndex = null;
  renderState();
}
async function refresh(selected) {
  const data = await api("session");
  state.molecules = data.molecules;
  selectMolecule(
    selected ||
      (state.molecules.some((m) => m.id === state.selected)
        ? state.selected
        : state.molecules.at(-1)?.id),
    !!selected || state.step !== "build" || !state.resultSelection,
  );
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
function selectEnergyPoint(event, _elements, chart) {
  if (
    state.busy ||
    state.mode !== "3d" ||
    state.step !== "optimize" ||
    !component
  )
    return;
  const area = chart.chartArea;
  if (
    !area ||
    event.x < area.left ||
    event.x > area.right ||
    event.y < area.top ||
    event.y > area.bottom
  )
    return;
  const x = chart.scales.x.getValueForPixel(event.x);
  const points = chart.data.datasets[0].data.filter((p) =>
    Number.isFinite(p.y),
  );
  if (!points.length) return;
  const point = points.reduce((a, b) =>
    Math.abs(a.x - x) <= Math.abs(b.x - x) ? a : b,
  );
  state.playbackMode = point.phase === "path" ? "path" : "optimization";
  const data = playbackData();
  const index = data.records.findIndex((p) =>
    point.phase === "path" ? p.image === point.image : p.step === point.x,
  );
  if (index >= 0) selectPlaybackFrame(index);
}
function renderEnergyHistory(activeStep) {
  let records = energyRecords();
  const initialOnly =
    !records.length && Number.isFinite(current()?.properties?.energy_ev);
  if (initialOnly)
    records = [
      {
        step: 0,
        energy_ev: current().properties.energy_ev,
        phase: "optimization",
      },
    ];
  $("energy-history").hidden = state.step !== "optimize" || !records.length;
  if (state.step !== "optimize" || !records.length) return;
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
    `${state.live?.phase === "vibration-preview" ? "Optimierung · " : ""}Schritt ${active.step}`;
  $("energy-reference").textContent =
    `ΔE relativ zu Schritt ${first.step}: E₀ = ${fmt(first.energy_ev, 6)} eV. `;
  if (initialOnly) {
    $("energy-history-value").textContent = "Ausgangsstruktur";
    $("energy-reference").textContent = "ΔE = 0 an der Ausgangsstruktur.";
  }
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
            pointRadius: 2,
            pointHoverRadius: 5,
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
        onClick: selectEnergyPoint,
        interaction: { mode: "nearest", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              title: (items) =>
                items[0].raw.phase === "path"
                  ? `Struktur auf dem Reaktionspfad ${items[0].raw.image + 1}`
                  : `${{ endpoint: "Anderes Minimum", path_seed: "Pfadvorbereitung", neb: "Weg optimieren", neb_climb: "Energiebarriere suchen", connectivity: "Verbindungsprüfung", complete: "Prüfung abgeschlossen", refinement: "Übergangszustand genauer bestimmen", vibrations: "Schwingungsprüfung" }[items[0].raw.phase] || "Optimierung"} · Schritt ${items[0].raw.x}`,
              label: (item) =>
                `E = ${fmt(item.raw.energy, 6)} eV · ΔE = ${fmt(item.raw.y, 4)} eV (${fmt(item.raw.y * EV_KJ, 1)} kJ/mol)`,
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
  });
  energyChart.data.datasets[0].data =
    OptimizationProgress.energyPoints(records);
  energyChart.data.datasets[1].data =
    state.live?.phase === "vibration-preview" ? [] : [point(active)];
  energyChart.options.scales.x.title.text = path?.length
    ? "Weg von der Ausgangsform (0) zur anderen Form (1)"
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
      "ΔE relativ zum Ausgangsminimum. Reaktionspfad zwischen den Minima, keine Zeitachse.";
    $("energy-history-value").textContent = pathActive
      ? `Struktur auf dem Reaktionspfad ${pathActive.image + 1} / ${path.length}`
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
      sourceId: state.selected,
      visibleSince: null,
      visibleSteps: new Set(),
    };
  const track = state.tracking;
  track.status = job.status;
  track.records = OptimizationProgress.merge(track.records, [
    ...parsed.records,
    ...(job.result?.molecule?.optimization_history || []),
  ]);
  track.sourceId = track.records[0]?.source_id || track.sourceId;
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
  $("job-status").hidden = false;
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
  if (state.step !== "optimize") return;
  if (!progress || progress.source_id !== current()?.id) return;
  if (state.busy) stopAnimation();
  renderPlaybackControls();
  $("properties-grid").style.visibility = "visible";
  $("properties-context").style.visibility = "visible";
  $("property-help").style.visibility = "visible";
  for (const id of ["xyz-download", "xyz-copy", "trajectory-download"])
    $(id).disabled = true;
  $("image-download").disabled = !current();
  const in3D = state.mode === "3d";
  const displayed = in3D
    ? {
        ...OptimizationProgress.geometryProperties(
          progress.positions,
          current().geometry_definition,
        ),
        energy_ev:
          progress.phase === "vibration-preview" ? null : progress.energy_ev,
      }
    : current().properties;
  for (const [id, key, digits] of [
    ["energy", "energy_ev", 4],
    ["dihedral", "dihedral_deg", 1],
    ["distance", "ring_distance_pm", 1],
  ]) {
    $(id).textContent = Number.isFinite(displayed?.[key])
      ? fmt(displayed[key], digits)
      : "—";
  }
  $("properties-context").hidden = false;
  $("properties-context").textContent = !in3D
    ? "Werte der ausgewählten Struktur"
    : progress.phase === "vibration-preview"
      ? "Werte der gezeigten Bewegung · Für diese verformten Strukturen wurde keine Energie berechnet."
      : "Werte der aktuell gezeigten Struktur";
  $("geometry-badge").textContent = in3D
    ? Number.isInteger(progress.neb_image)
      ? `${progress.replay ? "Wiedergabe" : "Live"} · Struktur auf dem Reaktionspfad ${progress.neb_image + 1}`
      : progress.phase === "vibration-preview"
        ? "Wiedergabe · Bewegung am Übergangszustand"
        : progress.replay
          ? "Wiedergabe · Zwischenschritt"
          : "Live · Zwischenschritt"
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
  $("job-status").hidden =
    job.status === "complete" ||
    (state.step === "build" && job.kind !== "template");
  if (job.kind !== "template") state.hasCalculationLog = true;
  $("calculation-log").hidden =
    state.step === "build" || !state.hasCalculationLog;
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
  const structureStatus = {
    complete: "Struktur erstellt",
    failed: "Struktur konnte nicht erstellt werden",
    cancelled: "Erstellen abgebrochen",
    timeout: "Das Erstellen dauert zu lange",
  };
  $("job-title").textContent =
    (job.kind === "template"
      ? structureStatus[job.status]
      : terminal[job.status]) || JOBS[job.kind];
  $("job-time").textContent =
    job.status === "queued"
      ? job.kind === "template"
        ? "Struktur wird vorbereitet …"
        : "Wartet auf einen freien Rechenplatz …"
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
        selectMolecule(progress.source_id);
        renderState();
      }
      applyLiveGeometry();
      if (component && state.mode === "3d" && state.step !== "spectrum") {
        state.tracking.visibleSince ??= performance.now();
        state.tracking.visibleSteps.add(progress.step);
      }
      $("job-time").textContent =
        `${fmt(job.elapsed || 0, 0)} s · Schritt ${progress.step} · E = ${fmt(progress.energy_ev, 4)} eV`;
      const phaseTitle = {
        endpoint: "Andere Form (cis oder trans) optimieren",
        path_seed: "Weg zwischen cis und trans vorbereiten",
        neb: "Strukturen auf dem Weg zwischen cis und trans optimieren",
        neb_climb: "Energiebarriere zwischen cis und trans suchen",
        connectivity: "Prüfen, ob beide Seiten zu cis und trans führen",
        complete: "Prüfung des Übergangszustands abgeschlossen",
        refinement: "Übergangszustand genauer bestimmen",
        vibrations: "Mögliche Bewegungen der Atome prüfen",
      }[progress.phase];
      if (phaseTitle) $("job-title").textContent = phaseTitle;
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
              "Die Optimierung ist noch nicht abgeschlossen. Die letzte Anordnung der Atome wurde gespeichert. Optimieren Sie diese erneut, bevor Sie ein Spektrum berechnen.",
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
  if (payload.kind === "minimum" && current()?.kind === "minimum")
    throw new Error(
      "Diese Struktur ist bereits ein Minimum. Der vorhandene Verlauf bleibt erhalten.",
    );
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
  if (["minimum", "ts"].includes(payload.kind)) {
    state.tracking = {
      sourceId: state.selected,
      status: "queued",
      records: [],
    };
    renderEnergyHistory();
  }
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
function structureGroups(molecules, query = "") {
  const groups = new Map();
  for (const m of molecules) {
    const name = m.base_name.replace(/^(cis|trans)-/, "");
    if (!groups.has(name))
      groups.set(name, { name, formula: m.formula, entries: [] });
    const configuration = m.base_name.match(/^(cis|trans)-/)?.[1] || "";
    const label =
      m.kind === "ts"
        ? `Übergangszustand · aus ${configuration}-Minimum`
        : `${configuration} · ${KIND[m.kind]}`;
    groups.get(name).entries.push({ molecule: m, label });
  }
  const search = query.trim().toLocaleLowerCase("de-DE");
  return [...groups.values()]
    .map((group) => {
      const totals = new Map(),
        counts = new Map();
      for (const entry of group.entries)
        totals.set(entry.label, (totals.get(entry.label) || 0) + 1);
      const entries = group.entries
        .map((entry) => {
          const n = (counts.get(entry.label) || 0) + 1;
          counts.set(entry.label, n);
          return {
            ...entry,
            label: entry.label + (totals.get(entry.label) > 1 ? ` · ${n}` : ""),
          };
        })
        .filter((entry) =>
          `${group.name} ${group.formula} ${entry.label}`
            .toLocaleLowerCase("de-DE")
            .includes(search),
        );
      return { ...group, entries };
    })
    .filter((group) => group.entries.length);
}
function renderStructureOptions() {
  const query = $("structure-search").value.trim().toLocaleLowerCase("de-DE");
  $("structure-options").replaceChildren();
  for (const group of structureGroups(selectableMolecules(), query)) {
    const section = document.createElement("section");
    section.className = "structure-group";
    const heading = document.createElement("h3");
    heading.textContent = group.name;
    const formula = document.createElement("p");
    formula.className = "structure-group-formula";
    formula.textContent = group.formula;
    section.append(heading, formula);
    for (const { molecule: m, label } of group.entries) {
      const row = document.createElement("div");
      row.className = "structure-row";
      const button = document.createElement("button");
      button.className = "structure-option";
      button.classList.toggle("selected", m.id === state.selected);
      if (m.id === state.selected) button.setAttribute("aria-current", "true");
      const name = document.createElement("strong");
      name.textContent = label;
      button.setAttribute("aria-label", `${group.name} · ${label}`);
      button.append(name);
      button.onclick = () => {
        if (state.busy) return;
        state.live = null;
        selectMolecule(m.id, state.step !== "build" || m.id !== state.selected);
        error("");
        renderState();
        $("structure-picker").close();
      };
      const remove = document.createElement("button");
      remove.className = "structure-delete";
      remove.type = "button";
      remove.title = "Struktur löschen";
      remove.setAttribute("aria-label", `${group.name} · ${label} löschen`);
      remove.innerHTML =
        '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7"/></svg>';
      remove.disabled = state.busy;
      remove.onclick = handle(async () => {
        if (state.busy || remove.disabled) return;
        remove.disabled = true;
        try {
          await api(`molecules/${m.id}`, { method: "DELETE" });
          await refresh();
          renderStructureOptions();
          $("structure-search").focus();
          toast("Struktur gelöscht.");
        } finally {
          remove.disabled = state.busy;
        }
      });
      row.append(button, remove);
      section.append(row);
    }
    $("structure-options").append(section);
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

$("build-view-toggle").onchange = (event) => {
  if (state.step !== "build" || current()?.kind !== "initial") return;
  state.buildMode = event.target.value;
  renderState();
};

$("clear-structures").onclick = handle(async () => {
  if (state.busy || !state.molecules.length) return;
  if (
    !window.confirm(
      "Alle Startstrukturen, Minima, Übergangszustände und Spektren dieser Sitzung löschen? Dies gilt auch für ausgeblendete Strukturen und kann nicht rückgängig gemacht werden.",
    )
  )
    return;
  $("clear-structures").disabled = true;
  try {
    await api("molecules", { method: "DELETE" });
    stopAnimation();
    state.selected = state.resultSelection = null;
    state.live = state.tracking = null;
    state.previewIndex = null;
    await refresh();
    $("structure-picker").close();
    (state.step === "build"
      ? $("create")
      : document.querySelector('[data-step="build"]')
    ).focus();
    toast("Alle Strukturen gelöscht.");
  } finally {
    updateControls();
  }
});

document
  .querySelectorAll("[data-step]")
  .forEach((button) => (button.onclick = () => navigate(button.dataset.step)));
$("center").onclick = () => {
  if (component) {
    component.autoView(0);
    stage.viewerControls.zoom(0.35);
  }
};
function selectPlaybackFrame(index) {
  if (state.busy || state.mode !== "3d" || state.step !== "optimize") return;
  stopAnimation();
  showFrame(index);
}
$("energy-chart").onkeydown = (event) => {
  const data = playbackData();
  if (!data.frames.length || state.busy || state.mode !== "3d") return;
  let index = state.previewIndex ?? data.frames.length - 1;
  if (event.key === "Home") index = 0;
  else if (event.key === "End") index = data.frames.length - 1;
  else if (event.key === "ArrowLeft") index--;
  else if (event.key === "ArrowRight") index++;
  else return;
  event.preventDefault();
  selectPlaybackFrame(Math.max(0, Math.min(index, data.frames.length - 1)));
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
    if (!stage || !component)
      throw new Error("3D-Modell ist noch nicht bereit.");
    const imageName = filename("png");
    download(
      await stage.makeImage({ factor: 2, antialias: true, trim: false }),
      imageName,
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
  for (const key of Object.keys(TITLES)) $("guide-" + key).open = key === step;
  $("guide").showModal();
  if (step) {
    const section = $("guide-" + step);
    section.open = true;
    section.scrollIntoView({ block: "start" });
  } else $("guide").scrollTop = 0;
}
$("guide-open").onclick = handle(() => guide(state.step));
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
        summarizeSubstituents();
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
