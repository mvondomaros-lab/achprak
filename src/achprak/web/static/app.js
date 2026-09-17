"use strict";
const $ = (id) => document.getElementById(id);
const SUBS = ["H", "Me", "OMe", "NMe2", "CF3", "CN", "NO2"];
function substituentLabel(text) {
  return text.replace(/\b(?:NMe2|OMe|Me|CF3|NO2)\b/g, (sub) =>
    ({ Me: "CH₃", OMe: "OCH₃", NMe2: "N(CH₃)₂", CF3: "CF₃", NO2: "NO₂" })[sub],
  );
}
for (let r = 0; r < 2; r++) {
  const field = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = r ? "Zweiter Ring" : "Erster Ring";
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
    SUBS.forEach((s) => select.add(new Option(substituentLabel(s), s)));
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
    "Spektrum berechnen",
    "Berechnen Sie die elektronischen Anregungsenergien und das UV/Vis-Spektrum einer optimierten Minimumstruktur.",
  ],
};
const JOBS = {
  template: "Struktur wird erstellt",
  minimum: "Minimumstruktur wird gesucht",
  ts: "Übergangsstruktur wird gesucht",
  uvvis: "UV/Vis-Spektrum wird berechnet",
};
const KIND = {
  initial: "Startstruktur",
  minimum: "Minimumstruktur",
  ts: "Übergangsstruktur",
  unconverged: "Optimierung nicht abgeschlossen",
};
const HC = 1239.8419843320026,
  EV_KJ = 96.48533212331002;
const current = () => state.molecules.find((m) => m.id === state.selected);
function selectableMolecules() {
  if (state.step === "build")
    return state.molecules.filter((m) => m.kind === "initial");
  if (state.step === "spectrum")
    return state.molecules.filter((m) => m.kind === "minimum");
  return state.molecules;
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
  const candidates = selectableMolecules();
  let preferred = state.step === "build" ? startingStructure(molecule) : molecule;
  if (state.step === "spectrum" && molecule?.kind === "ts")
    preferred = candidates.find((m) => m.id === molecule.parent_id);
  state.selected =
    candidates.find((m) => m.id === preferred?.id)?.id ||
    candidates.at(-1)?.id ||
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
    (current() ? structureLabel(current()) : "photoschalter")
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
  for (const id of ["play", "energy-play"]) {
    $(id).textContent = "Abspielen";
    $(id).setAttribute("aria-label", "Verlauf einmal abspielen");
  }
}
function playbackData() {
  const molecule = current();
  if (molecule?.ts_search?.path?.length)
    return OptimizationProgress.playback(molecule, [], "path");
  if (molecule?.ts_search)
    return { kind: "path", frames: [], records: [] };
  const records = energyRecords().filter((p) => p.phase === "optimization");
  return OptimizationProgress.playback(molecule, records, "optimization");
}
function renderPlaybackControls() {
  const data = playbackData();
  const unavailable =
    state.busy || state.mode !== "3d" || !component || !data.frames.length;
  for (const id of ["play", "energy-play"]) {
    $(id).hidden = state.step !== "optimize" || !data.frames.length;
    $(id).disabled = unavailable;
  }
  $("energy-chart").setAttribute("aria-disabled", String(unavailable));
  $("plot-hint").hidden = unavailable;
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
      data.kind === "path" ? "path" : data.records[index]?.phase || "optimization",
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
      // NGL's 10 Å camera clearance clips small molecules during close-up zoom.
      clipDist: 0.1,
      // Start fog beyond the visible scene, preserving colours at every depth.
      fogNear: 100,
      fogFar: 200,
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
  $("center").hidden = state.mode !== "3d";
  $("viewport").hidden = state.mode !== "3d";
  $("structure-image").hidden = state.mode !== "2d" || !current();
  $("viewer-hint").hidden = !current() || state.mode !== "3d";
  $("center").disabled = !current() || state.mode !== "3d";
  $("properties-grid").hidden = state.step !== "optimize" || !current();
  $("properties-grid").style.visibility = "visible";
  $("properties-context").hidden = state.step !== "optimize" || !state.live;
  $("properties-context").style.visibility = "visible";
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
  const tsRestriction = m?.ts_restriction;
  const minimumRestriction = !tsSelected && m?.kind === "ts";
  $("ts-requirement").textContent = minimumRestriction
    ? "Eine Minimumsuche ausgehend von einer Übergangsstruktur ist hier nicht möglich. Wählen Sie eine Startstruktur."
    : tsRestriction || "Suchen Sie zuerst eine Minimumstruktur.";
  $("ts-requirement").hidden = !minimumRestriction && (!m || !tsSelected || (m.kind === "minimum" && !tsRestriction));
  $("optimize").disabled =
    state.busy ||
    !m ||
    (tsSelected && (m.kind !== "minimum" || !!tsRestriction)) ||
    (!tsSelected && ["minimum", "ts"].includes(m.kind));
  $("optimize").textContent =
    !tsSelected && m?.kind === "minimum"
      ? "Minimumstruktur bereits gefunden"
      : "Optimierung starten";
  const alreadyCreated = state.molecules.some(
    (molecule) =>
      molecule.kind === "initial" &&
      molecule.settings?.configuration ===
        document.querySelector("input[name=configuration]:checked").value &&
      molecule.settings.substituents.every((sub, i) => sub === $("sub-" + i).value),
  );
  $("create").disabled = state.busy || alreadyCreated;
  $("create").textContent = alreadyCreated
    ? "Struktur bereits erstellt"
    : "Struktur erstellen";
  $("molecule-select").disabled = state.busy || !selectableMolecules().length;
  $("clear-structures").disabled = state.busy || !state.molecules.length;
  $("calculate-spectrum").disabled = state.busy || m?.kind !== "minimum" || !!m?.spectrum;
  $("spectrum-requirement").hidden = m?.kind === "minimum";
  $("spectrum-requirement").textContent =
    "Suchen Sie zuerst in Schritt 02 eine Minimumstruktur.";
  $("calculate-spectrum").textContent = m?.spectrum
    ? "Spektrum bereits berechnet"
    : "Spektrum berechnen";
  $("structure-library").hidden = !selectableMolecules().length;
  $("structure-picker-title").textContent =
    state.step === "build" ? "Startstruktur auswählen" : "Struktur auswählen";
  $("result-heading").hidden = !m;
  $("viewer-toolbar").hidden = !m;
  $("image-download").disabled = !m;
  updateMode();
}
function renderSpectrum() {
  const spec = current()?.spectrum;
  $("spectrum-empty").hidden = !!spec;
  $("spectrum-result").hidden = !spec;
  if (!spec) return;
  renderSolutionColor();
  if (state.step === "spectrum") renderSpectrumChart(spec);
  const peak = spec.absorption.indexOf(Math.max(...spec.absorption)),
    e = spec.energy_ev[peak];
  $("spectrum-caption").textContent =
    `Absorptionsmaximum im dargestellten Energiebereich: ${fmt(e, 4)} eV.` +
    (spec.coverage_complete === false
      ? " Am oberen Rand des dargestellten Energiebereichs fehlen möglicherweise Beiträge weiterer Übergänge. Die Absorption in diesem Bereich kann dadurch unterschätzt werden."
      : "");

}
function renderSolutionColor() {
  const density = Number($("solution-color-density").value);
  const result = SolutionColor.estimate(current()?.spectrum, density);
  $("solution-color-density-value").textContent = fmt(density, 1);
  $("solution-color-density").setAttribute("aria-valuetext", `Faktor ${fmt(density, 1)}`);
  $("solution-color-sample").textContent = `${structureLabel(current())} · nur ausgewählte Struktur`;
  const swatch = $("solution-color-swatch");
  swatch.hidden = !result;
  swatch.style.backgroundColor = result?.css || "";
  swatch.setAttribute("aria-label", `Geschätzte Lösungsfarbe für ${structureLabel(current())}, Faktor ${fmt(density, 1)}`);
  $("solution-color-status").textContent = result
    ? `Lichtdurchlässigkeit, gewichtet nach der Helligkeitsempfindlichkeit des Auges: ${fmt(100 * result.luminance, 1)} %`
    : "Keine Farbschätzung verfügbar: Das Spektrum ist unvollständig oder enthält keine auswertbaren Absorptionsdaten.";
}
$("solution-color-density").addEventListener("input", renderSolutionColor);

function renderState() {
  const m = current();
  if (state.playbackMolecule !== m?.id) {
    stopAnimation();
    state.playbackMolecule = m?.id;
    state.previewIndex = null;
  }
  if (state.live && state.live.source_id !== m?.id) state.live = null;
  $("molecule-select").textContent = m
    ? structureGroupLabel(m)
    : "Noch keine Struktur";
  $("molecule-select").title = m ? structureGroupLabel(m) : "Struktur auswählen";
  $("structure-count").textContent = String(
    structureGroups(selectableMolecules()).length,
  );
  $("active-name").textContent = m ? structureGroupLabel(m) : "Startstruktur";
  $("active-meta").textContent = m
    ? `${m.formula} · ${m.atom_count} Atome`
    : "Wählen Sie cis oder trans. Substituenten können Sie bei Bedarf ergänzen.";
  $("geometry-badge").hidden = !m;
  $("geometry-badge").textContent = m ? KIND[m.kind] : "";
  $("geometry-badge").classList.remove("live", "playback");
  for (const kind of ["initial", "minimum", "ts"])
    $("geometry-badge").classList.toggle(kind, m?.kind === kind);
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
      ? `Elektronische Energiebarriere ΔE‡: ${fmt(ts.barrier_ev, 4)} eV`
      : "Übergangsstruktur noch nicht bestätigt.";
  $("ts-details").hidden = state.step !== "optimize" || !ts;
  $("ts-check-result").textContent = !ts
    ? ""
    : ts.connectivity?.verified
      ? `Die Minimumsuche ausgehend von beiden Seiten der Übergangsstruktur erreicht eine cis- und eine trans-Minimumstruktur.${ts.connectivity.endpoint_conformers_match ? "" : " Die erreichten Minimumstrukturen haben anders angeordnete Ringe oder Substituenten als die Minimumstrukturen am Anfang und Ende des dargestellten Reaktionspfads."} Die elektronische Energiebarriere gilt für den untersuchten Reaktionspfad; Temperatureffekte sind nicht berücksichtigt.`
      : "Die Verbindung zwischen cis und trans wurde nicht bestätigt. Besprechen Sie das Ergebnis mit Ihrer Betreuung.";
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
  updateGuide(step);
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
async function refresh(selected, finishCalculation = false) {
  const data = await api("session");
  // Keep the live view intact until the complete result is available.
  if (finishCalculation) {
    state.live = null;
    state.busy = false;
  }
  state.molecules = data.molecules;
  selectMolecule(
    selected ||
      (state.molecules.some((m) => m.id === state.selected)
        ? state.selected
        : state.molecules.at(-1)?.id),
    !!selected || state.step !== "build" || !state.resultSelection,
  );
  $("hub-logout").hidden = !data.hub?.logout;
  $("hub-logout").href = data.hub?.logout || "";
  $("hub-logout").title = data.user ? `Angemeldet als ${data.user}` : "";
  $("hub-logout").ariaLabel = data.user ? `Abmelden (${data.user})` : "Abmelden";
  renderState();
  return data;
}
let energyChart = null;
let spectrumChart = null;
// Keep aligned with the Matplotlib spectrum style in web/worker.py.
const plotStyle = {
  font: { family: "Arial, Helvetica, sans-serif", size: 16 },
  titleFont: { family: "Arial, Helvetica, sans-serif", size: 17 },
  text: "#586b80",
  border: "#dce4ed",
  grid: "#e7edf5",
};
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
  const data = playbackData();
  const index = data.records.findIndex((p) =>
    point.phase === "path" ? p.image === point.image : p.step === point.x,
  );
  if (index >= 0) selectPlaybackFrame(index);
}
function renderEnergyHistory(activeStep) {
  const records = energyRecords();
  const active = records.find((p) => p.step === activeStep) || records.at(-1);
  const path = state.busy
    ? records.findLast((p) => p.step <= (active?.step ?? Infinity) && p.neb_path)?.neb_path
    : current()?.ts_search?.path;
  const exploringTS = state.busy && state.tracking?.kind === "ts" &&
    state.tracking.sourceId === state.selected;
  const searchRecords = records.filter((p) =>
    (exploringTS || p.phase === "optimization") && Number.isFinite(p.energy_ev),
  );
  const pendingSearch = state.busy && ["minimum", "ts"].includes(state.tracking?.kind) &&
    state.tracking.sourceId === state.selected;
  const visible = state.step === "optimize" &&
    (!!path?.length || searchRecords.length > 0 || pendingSearch);
  $("energy-history").hidden = !visible;
  if (!visible) return;
  const pathActive = state.live?.phase === "path" ? state.live : null;
  const live = state.busy;
  $("energy-history-state").textContent = live ? "· Live" : "";
  const source = current()?.base_name?.match(/^(cis|trans)-/)?.[1];
  const direction = source ? ` · ${source} → ${source === "cis" ? "trans" : "cis"}` : "";
  $("energy-path-meta").textContent = path?.length
    ? `Reaktionspfad im elektronischen Grundzustand${direction}`
    : exploringTS ? "Übergangsstruktursuche · Vorbereitung des Reaktionspfads"
      : "Minimumsuche · Energie der Optimierungsschritte";
  $("energy-history").setAttribute("aria-label",
    path?.length ? "Energieprofil des Reaktionspfads" : "Energieverlauf der Suche");
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
            label: "Dargestellte Struktur",
            data: [],
            borderColor: "#c77825",
            backgroundColor: "#c77825",
            pointRadius: 4,
            showLine: false,
          },
        ],
      },
      options: {
        locale: "de-DE",
        color: plotStyle.text,
        font: plotStyle.font,
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        parsing: false,
        onClick: selectEnergyPoint,
        interaction: { mode: "nearest", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            titleFont: plotStyle.titleFont,
            bodyFont: plotStyle.font,
            backgroundColor: "#192d43",
            padding: 10,
            callbacks: {
              title: (items) =>
                items[0].raw.phase === "path"
                  ? `Struktur auf dem Reaktionspfad ${items[0].raw.image + 1}`
                  : `${{ endpoint: "Andere Minimumstruktur", path_seed: "Pfadvorbereitung", neb: "Reaktionspfad optimieren", neb_climb: "Energiebarriere suchen", connectivity: "Verbindungsprüfung", complete: "Prüfung abgeschlossen", refinement: "Geometrie der Übergangsstruktur verfeinern", vibrations: "Schwingungsprüfung" }[items[0].raw.phase] || "Optimierung"} · Schritt ${items[0].raw.x}`,
              label: (item) =>
                `E = ${fmt(item.raw.energy, 4)} eV · ΔE = ${fmt(item.raw.y, 4)} eV (${fmt(item.raw.y * EV_KJ, 1)} kJ/mol)`,
            },
          },
        },
        scales: {
          x: {
            type: "linear",
            title: {
              display: true, text: "Suchschritt", color: plotStyle.text,
              font: plotStyle.titleFont, padding: { top: 10, bottom: 0 },
            },
            ticks: {
              precision: 0, maxTicksLimit: 7, maxRotation: 0,
              color: plotStyle.text, font: plotStyle.font, padding: 8,
            },
            grid: { display: false, drawTicks: false },
            border: { color: plotStyle.border },
          },
          y: {
            title: {
              display: true, text: "ΔE / eV", color: plotStyle.text,
              font: plotStyle.titleFont, padding: { top: 0, bottom: 10 },
            },
            ticks: {
              maxTicksLimit: 5, color: plotStyle.text, callback: (value) => fmt(value, 4),
              font: plotStyle.font, padding: 8,
            },
            grid: { color: plotStyle.grid, lineWidth: 1, drawTicks: false },
            border: { color: plotStyle.border },
          },
        },
      },
    });
  }
  energyChart.options.scales.x.title.text = path?.length ? "Reaktionspfad" : exploringTS ? "Suchschritt" : "Optimierungsschritt";
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
      (state.busy && active?.neb_path
        ? path.find((p) => p.image === active.neb_image)
        : null) ||
      path.reduce((a, b) => (a.energy_ev > b.energy_ev ? a : b));
    energyChart.data.datasets[1].data = selected ? [pathPoint(selected)] : [];
    $("energy-reference").textContent =
      "ΔE relativ zum Ausgangsstruktur · keine Zeitachse.";
    $("energy-chart").setAttribute(
      "aria-label",
      `Energieprofil des Reaktionspfads mit ${path.length} Strukturen`,
    );
  } else {
    const reference = searchRecords[0]?.energy_ev ?? 0;
    const point = (p) => ({
      x: p.step, y: p.energy_ev - reference, energy: p.energy_ev,
      phase: p.phase,
    });
    energyChart.data.datasets[0].data = searchRecords.map(point);
    const selected = searchRecords.find((p) => p.step === activeStep) || searchRecords.at(-1);
    energyChart.data.datasets[1].data = selected ? [point(selected)] : [];
    $("energy-reference").textContent = exploringTS
      ? "ΔE relativ zum ersten Suchschritt · noch kein Reaktionspfad."
      : "ΔE relativ zum ersten Optimierungsschritt · keine Zeitachse.";
    $("energy-chart").setAttribute("aria-label",
      `Energieverlauf der Suche mit ${searchRecords.length} Schritten`);
  }
  energyChart.update("none");
}
function renderSpectrumChart(spec) {
  const min = spec.energy_ev[0], max = spec.energy_ev.at(-1);
  if (!spectrumChart) {
    const title = (text) => ({ display: true, text, color: plotStyle.text,
      font: plotStyle.titleFont, padding: 10 });
    const ticks = { color: plotStyle.text, font: plotStyle.font, padding: 8,
      maxRotation: 0, maxTicksLimit: 7 };
    spectrumChart = new Chart($("spectrum-chart"), {
      type: "line",
      data: { datasets: [
        { label: "Verbreiterte Banden", order: 1, data: [], borderColor: "#165de1",
          borderWidth: 2, pointRadius: 0, tension: 0 },
        { label: "Diskrete Übergänge", data: [], borderColor: "#c77825",
          borderWidth: 1.5, backgroundColor: "#c77825",
          pointRadius: (context) => context.dataIndex % 3 === 1 ? 3 : 0,
          pointHoverRadius: (context) => context.dataIndex % 3 === 1 ? 5 : 0,
          spanGaps: false },
        { label: "Ausgewählter Übergang", order: -1, data: [], borderColor: "#995511",
          backgroundColor: "#995511", borderWidth: 3, pointRadius: [0, 4] },
      ] },
      options: {
        locale: "de-DE", color: plotStyle.text, font: plotStyle.font,
        responsive: true, maintainAspectRatio: false, animation: false, parsing: false,
        onClick: selectSpectrumTransition,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: {
          x: { type: "linear", title: title("Energie / eV"), ticks: { ...ticks, callback: (value) => fmt(value, 4) },
            grid: { display: false, drawTicks: false }, border: { color: plotStyle.border } },
          wavelength: { type: "linear", position: "top", title: title("Wellenlänge / nm"),
            afterBuildTicks: (axis) => { axis.ticks = [800, 600, 500, 400, 300, 250]
              .map((nm) => ({ value: HC / nm }))
              .filter((tick) => tick.value >= axis.min && tick.value <= axis.max); },
            ticks: { ...ticks, autoSkip: false, callback: (value) => fmt(HC / value, 0) },
            grid: { display: false, drawTicks: false }, border: { display: false } },
          y: { title: title("Relative Absorption"), beginAtZero: true,
            ticks: { ...ticks, maxTicksLimit: 5 },
            grid: { color: plotStyle.grid, lineWidth: 1, drawTicks: false },
            border: { color: plotStyle.border } },
        },
      },
    });
  }
  if (spectrumChart.spectrumData !== spec) {
    spectrumChart.data.datasets[2].data = [];
    $("spectrum-selection").textContent = "Wählen Sie eine orange Linie oder ihre Markierung, um Anregungsenergie, Wellenlänge und Oszillatorstärke abzulesen.";
  }
  spectrumChart.spectrumData = spec;
  spectrumChart.data.datasets[0].data = spec.energy_ev.map((x, i) => ({ x, y: spec.absorption[i] }));
  spectrumChart.data.datasets[1].data = spec.excitations_ev.flatMap((x, i) =>
    x < min || x > max ? [] : [{ x, y: 0 }, { x, y: spec.oscillator_strengths[i] }, { x, y: null }]);
  for (const id of ["x", "wavelength"]) {
    spectrumChart.options.scales[id].min = min;
    spectrumChart.options.scales[id].max = max;
  }
  spectrumChart.update("none");
}
function selectSpectrumTransition(event, _elements, chart) {
  const area = chart.chartArea, spec = chart.spectrumData;
  if (!area || !spec || event.x < area.left || event.x > area.right ||
      event.y < area.top || event.y > area.bottom) return;
  const axis = chart.scales.x;
  const candidates = spec.excitations_ev.map((energy, index) => ({ energy, index,
    distance: Math.abs(axis.getPixelForValue(energy) - event.x) }))
    .filter((p) => p.energy >= axis.min && p.energy <= axis.max && p.distance <= 12)
    .sort((a, b) => a.distance - b.distance);
  if (!candidates.length) return;
  const { energy, index } = candidates[0];
  const strength = spec.oscillator_strengths[index];
  chart.data.datasets[2].data = [{ x: energy, y: 0 }, { x: energy, y: strength }];
  $("spectrum-selection").textContent = `Übergang ${index + 1} · ${fmt(energy, 4)} eV · ${fmt(HC / energy, 1)} nm · Oszillatorstärke: ${fmt(strength, 4)}`;
  chart.update("none");
}
function collectProgress(job) {
  if (!["minimum", "ts"].includes(job.kind)) return;
  const parsed = OptimizationProgress.parse(job.log || "");
  if (state.tracking?.jobId !== job.id)
    state.tracking = {
      jobId: job.id,
      kind: job.kind,
      records: [],
      sourceId: state.selected,
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
function applyLiveGeometry() {
  const progress = state.live;
  if (state.step !== "optimize") return;
  if (!progress || progress.source_id !== current()?.id) return;
  if (state.busy) stopAnimation();
  renderPlaybackControls();
  $("properties-grid").style.visibility = "visible";
  $("properties-context").style.visibility = "visible";
  $("image-download").disabled = !current();
  const in3D = state.mode === "3d";
  const displayed = in3D
    ? {
        ...OptimizationProgress.geometryProperties(
          progress.positions,
          current().geometry_definition,
        ),
        energy_ev: progress.energy_ev,
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
  const displayStatus = progress.replay ? "Wiedergabe" : "Berechnung läuft";
  $("properties-context").textContent = !in3D
    ? "Werte der Ausgangsstruktur · 2D"
    : Number.isInteger(progress.neb_image)
      ? `${displayStatus} · Werte der Struktur auf dem Reaktionspfad ${progress.neb_image + 1}`
      : `${displayStatus} · Werte des Zwischenschritts ${progress.step}`;
  $("geometry-badge").hidden = false;
  $("geometry-badge").textContent = in3D
    ? progress.replay ? "Wiedergabe" : "Live"
    : "Ausgangsstruktur · 2D";
  $("geometry-badge").classList.remove("initial", "minimum", "ts");
  $("geometry-badge").classList.toggle("live", in3D && state.busy && !progress.replay);
  $("geometry-badge").classList.toggle("playback", in3D && !!progress.replay);
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
    (job.status === "complete" && !state.busy) ||
    (state.step === "build" && job.kind !== "template");
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
    cancelled: "Strukturerstellung abgebrochen",
    timeout: "Zeitlimit für die Strukturerstellung erreicht",
  };
  $("job-title").textContent =
    (job.kind === "template"
      ? structureStatus[job.status]
      : terminal[job.status]) || JOBS[job.kind];
  $("job-time").textContent =
    job.status === "queued"
      ? job.kind === "template"
        ? "Struktur wird vorbereitet …"
        : "Berechnung wartet auf verfügbare Rechenkapazität …"
      : `${fmt(job.elapsed || 0, 0)} s`;
  $("job-detail").hidden = job.kind !== "uvvis" || job.status !== "running";
  if (!$("job-detail").hidden) {
    const description = SpectrumProgress.describe(job.spectrum_progress?.phase, job.elapsed);
    $("job-title").textContent = description.title;
    $("job-detail").textContent = description.detail;
  }
  $("cancel").hidden = !["queued", "running"].includes(job.status);
  if (job.log !== undefined) {
    const progress = collectProgress(job);
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
      $("job-time").textContent =
        `${fmt(job.elapsed || 0, 0)} s · Schritt ${progress.step} · E = ${fmt(progress.energy_ev, 4)} eV`;
      const phaseTitle = {
        endpoint: "Minimumstruktur der anderen cis/trans-Konfiguration suchen",
        path_seed: "Reaktionspfad zwischen cis und trans vorbereiten",
        neb: "Strukturen entlang des Reaktionspfads optimieren",
        neb_climb: "Energiebarriere zwischen cis und trans suchen",
        connectivity: "Verbindung der Übergangsstruktur zu cis- und trans-Minimumstrukturen prüfen",
        complete: "Prüfung der Übergangsstruktur abgeschlossen",
        refinement: "Geometrie der Übergangsstruktur verfeinern",
        vibrations: "Schwingungsfrequenzen zur Prüfung der Übergangsstruktur berechnen",
      }[progress.phase];
      if (phaseTitle) $("job-title").textContent = phaseTitle;
    }
  }
  renderEnergyHistory(state.live?.step);
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
        if (job.kind === "template" && job.result?.molecule?.id)
          state.buildMode = "2d";
        await refresh(job.result?.molecule?.id, true);
        displayJob(job);
        if (job.error) error(job.error);
        if (job.result?.molecule?.converged === false)
          error(
            job.result.molecule.ts_search?.failure_reason ||
              "Die Optimierung ist noch nicht abgeschlossen. Die zuletzt berechnete Struktur wurde gespeichert. Suchen Sie ausgehend davon eine Minimumstruktur, bevor Sie ein Spektrum berechnen.",
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
  if (payload.kind === "uvvis" && current()?.spectrum)
    throw new Error("Für diese Minimumstruktur wurde bereits ein Spektrum berechnet.");
  if (payload.kind === "minimum" && current()?.kind === "minimum")
    throw new Error(
      "Diese Struktur ist bereits eine Minimumstruktur. Der vorhandene Verlauf bleibt erhalten.",
    );
  if (payload.kind === "minimum" && current()?.kind === "ts")
    throw new Error("Eine Minimumsuche ausgehend von einer Übergangsstruktur ist hier nicht möglich. Wählen Sie eine Startstruktur.");
  if (state.busy)
    throw new Error("Warten Sie, bis die laufende Berechnung abgeschlossen ist.");
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
      kind: payload.kind,
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
$("builder").addEventListener("change", updateControls);
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
$("cancel").onclick = handle(async () => {
  if (state.job) await api(`jobs/${state.job}`, { method: "DELETE" });
});
function structureIdentity(molecule) {
  const base = molecule.base_name || "";
  const configuration = base.match(/^(cis|trans)-/)?.[1] || "";
  const pattern = base.replace(/^(cis|trans)-/, "").replace(/-?Azobenzol$/, "");
  return {
    configuration,
    pattern: substituentLabel(pattern || "unsubstituiert"),
    isPath: molecule.kind === "ts" || !!molecule.ts_search,
  };
}
function structureGroupLabel(molecule) {
  const { configuration, pattern } = structureIdentity(molecule);
  return `${configuration} · ${pattern}`;
}
function structureLabel(molecule) {
  const { configuration, pattern, isPath } = structureIdentity(molecule);
  const direction = isPath
    ? `${configuration} → ${configuration === "cis" ? "trans" : "cis"}`
    : configuration;
  return `${direction}${molecule.kind === "ts" ? " Übergangsstruktur" : ""} · ${pattern}`;
}
function structureGroups(molecules, query = "") {
  const groups = new Map();
  for (const m of molecules) {
    const name = structureGroupLabel(m);
    if (!groups.has(name))
      groups.set(name, { name, formula: m.formula, entries: [] });
    const label = KIND[m.kind];
    const key = m.kind;
    const kindOrder = { initial: 0, minimum: 1, unconverged: 2, ts: 3 }[m.kind] ?? 4;
    groups.get(name).entries.push({
      molecule: m, label, key, order: kindOrder,
    });
  }
  const normalize = (text) => text.normalize("NFKC").trim().toLocaleLowerCase("de-DE");
  const search = normalize(query);
  return [...groups.values()]
    .map((group) => {
      const totals = new Map(), counts = new Map();
      for (const entry of group.entries)
        totals.set(entry.key, (totals.get(entry.key) || 0) + 1);
      const entries = group.entries
        .sort((a, b) => a.order - b.order)
        .map((entry) => {
          const n = (counts.get(entry.key) || 0) + 1;
          counts.set(entry.key, n);
          return {
            ...entry,
            label: entry.label + (totals.get(entry.key) > 1 ? ` · ${n}` : ""),
          };
        })
        .filter((entry) => normalize(
          `${group.name} ${group.formula} ${entry.label}`,
        ).includes(search));
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
    heading.textContent = substituentLabel(group.name);
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
      const accessibleLabel = `${group.name} · ${label}`;
      button.setAttribute("aria-label", accessibleLabel);
      const title = document.createElement("span");
      title.className = "structure-option-title";
      title.textContent = label;
      if (m.id === state.selected) {
        const check = document.createElement("span");
        check.textContent = "✓";
        check.setAttribute("aria-hidden", "true");
        title.append(check);
      }
      button.append(title);
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
      remove.setAttribute("aria-label", `${accessibleLabel} löschen`);
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
      "Alle Startstrukturen, Minimumstrukturen, Übergangsstrukturen und Spektren dieser Sitzung löschen? Dies gilt auch für ausgeblendete Strukturen und kann nicht rückgängig gemacht werden.",
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
$("play").onclick = $("energy-play").onclick = () => {
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
  for (const id of ["play", "energy-play"]) {
    $(id).textContent = "Pause";
    $(id).setAttribute("aria-label", "Wiedergabe pausieren");
  }
  animation = setInterval(() => {
    showFrame(++index);
    if (index >= count - 1) stopAnimation();
  }, 150);
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
$("energy-png").onclick = handle(async () => {
  if (!energyChart || !current()) return;
  stopAnimation();
  // Capture the visible plot and its reference before asynchronous encoding.
  const source = energyChart.canvas;
  const scale = source.width / energyChart.width;
  const header = Math.round(38 * scale);
  const footer = Math.round(34 * scale);
  const canvas = document.createElement("canvas");
  canvas.width = source.width;
  canvas.height = source.height + header + footer;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#192d43";
  ctx.font = `${16 * scale}px Arial, Helvetica, sans-serif`;
  ctx.fillText(structureLabel(current()), 12 * scale, 25 * scale,
    canvas.width - 24 * scale);
  ctx.drawImage(source, 0, header);
  ctx.fillStyle = plotStyle.text;
  ctx.font = `${12 * scale}px Arial, Helvetica, sans-serif`;
  ctx.fillText($("energy-reference").textContent, 12 * scale,
    header + source.height + 22 * scale, canvas.width - 24 * scale);
  const isPath = energyChart.data.datasets[0].data.some((p) => p.phase === "path");
  const name = filename(isPath ? "reaction-path.png" : "optimization-energy.png");
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!blob) throw new Error("Energieverlauf konnte nicht gespeichert werden.");
  download(blob, name);
});
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
$("spectrum-png").onclick = handle(async () => {
  if (!spectrumChart || !current()?.spectrum) return;
  const name = filename("spectrum.png");
  const source = spectrumChart.canvas;
  const scale = source.width / spectrumChart.width;
  const header = Math.round(38 * scale), footer = Math.round(34 * scale);
  const canvas = document.createElement("canvas");
  canvas.width = source.width;
  canvas.height = source.height + header + footer;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "white";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#192d43";
  ctx.font = `${16 * scale}px Arial, Helvetica, sans-serif`;
  ctx.fillText(structureLabel(current()), 12 * scale, 25 * scale, canvas.width - 24 * scale);
  ctx.drawImage(source, 0, header);
  ctx.fillStyle = plotStyle.text;
  ctx.font = `${12 * scale}px Arial, Helvetica, sans-serif`;
  ctx.fillText("Relative Absorption in willkürlichen Einheiten · INDO/S–CIS", 12 * scale,
    header + source.height + 22 * scale, canvas.width - 24 * scale);
  const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  if (!blob) throw new Error("Spektrum konnte nicht gespeichert werden.");
  download(blob, name);
});
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
        ? key === "ev" ? values[key].toFixed(4) : Number(values[key].toPrecision(9))
        : "";
}
for (const key of ["ev", "kj", "nm"])
  $("convert-" + key).oninput = () => convert(key);
convert("ev");
$("converter-open").onclick = () => $("converter").showModal();
function updateGuide(step) {
  for (const key of Object.keys(TITLES)) {
    const section = $("guide-" + key);
    if (!section) continue;
    section.hidden = key !== step;
  }
}
async function guide(step, focus = true) {
  if (!$("guide-content").children.length) {
    const response = await fetch("static/guide.html?v=ui-60");
    if (!response.ok) throw new Error("Aufgaben konnten nicht geladen werden. Öffnen Sie die Aufgaben erneut.");
    $("guide-content").innerHTML = await response.text(); // Trusted, bundled teaching material.
  }
  updateGuide(state.step);
  $("guide").hidden = false;
  $("guide-open").setAttribute("aria-expanded", "true");
  if (focus) $("guide-title").focus();
  window.dispatchEvent(new Event("resize"));
}
function closeGuide() {
  $("guide").hidden = true;
  $("guide-open").setAttribute("aria-expanded", "false");
  $("guide-open").focus();
  window.dispatchEvent(new Event("resize"));
}
$("guide-open").onclick = handle(() => $("guide").hidden ? guide(state.step) : closeGuide());
$("guide-close").onclick = closeGuide;
$("guide").addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    event.preventDefault();
    closeGuide();
  }
});
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

// Task loading must not delay restoration of calculations.
handle(() => guide(state.step, false))();
