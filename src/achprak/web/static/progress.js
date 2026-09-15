"use strict";
// Kept independent of the DOM so polling edge cases can be regression tested.
globalThis.OptimizationProgress = {
  energyPoints(records) {
    const baseline = records[0]?.energy_ev || 0;
    return records.flatMap((p) => {
      const point = {
        x: p.step,
        y: p.energy_ev - baseline,
        energy: p.energy_ev,
        phase: p.phase,
        attempt: p.attempt || 1,
      };
      // A restarted search is not a physical downhill segment of the path.
      return p.restart ? [{ ...point, y: null }, point] : [point];
    });
  },
  playback(molecule, records, mode) {
    const path = molecule?.ts_search?.path;
    if (mode === "path" && path?.length) {
      const points = path.map((p, i) => ({
        ...p,
        step: i,
        phase: "path",
        source_id: molecule.id,
      }));
      return {
        kind: "path",
        frames: points.map((p) => p.positions),
        records: points,
      };
    }
    const vibration = molecule?.trajectory_kind === "vibration";
    if (vibration && (mode === "vibration" || !records.length))
      return { kind: "vibration", frames: molecule.frames || [], records: [] };
    return {
      kind: "optimization",
      frames: records.length
        ? records.map((p) => p.positions)
        : molecule?.frames || [],
      records,
    };
  },
  valid(record) {
    return (
      record &&
      Number.isInteger(record.step) &&
      record.step >= 0 &&
      typeof record.source_id === "string" &&
      [
        "optimization",
        "scan",
        "refinement",
        "vibrations",
        "endpoint",
        "path_seed",
        "neb",
        "neb_climb",
        "connectivity",
        "complete",
      ].includes(record.phase) &&
      Number.isFinite(record.energy_ev) &&
      Number.isFinite(record.fmax_ev_angstrom) &&
      Array.isArray(record.positions) &&
      record.positions.length > 0 &&
      record.positions.length % 3 === 0 &&
      record.positions.every(Number.isFinite)
    );
  },
  parse(log) {
    const prefix = "ACHPRAK_PROGRESS ";
    const records = [],
      output = [];
    for (const line of log.split("\n")) {
      if (!line.startsWith(prefix)) {
        // A truncated first JSON record is not useful as human-readable output.
        if (output.length || !line.includes('"positions"')) output.push(line);
        continue;
      }
      try {
        const record = JSON.parse(line.slice(prefix.length));
        if (this.valid(record)) records.push(record);
      } catch {
        /* A later poll will finish a partially written record. */
      }
    }
    return { records, output: output.join("\n") };
  },
  merge(previous, incoming) {
    const steps = new Map();
    for (const record of [...previous, ...incoming]) {
      if (this.valid(record))
        steps.set(`${record.source_id}:${record.step}`, record);
    }
    return [...steps.values()].sort((a, b) => a.step - b.step);
  },
  shouldReplay(records, visibleSince, now, visibleSteps = Infinity) {
    return (
      records.length > 1 &&
      (!visibleSince ||
        now - visibleSince < 1500 ||
        visibleSteps < Math.min(4, records.length))
    );
  },
};
