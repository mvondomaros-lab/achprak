"use strict";
// Kept independent of the DOM so polling edge cases can be regression tested.
globalThis.OptimizationProgress = {
  geometryProperties(positions, definition) {
    if (!definition || !positions) return {};
    const at = (i) => positions.slice(3 * i, 3 * i + 3);
    const sub = (a, b) => a.map((v, i) => v - b[i]);
    const dot = (a, b) => a.reduce((s, v, i) => s + v * b[i], 0);
    const norm = (a) => Math.sqrt(dot(a, a));
    const cross = (a, b) => [
      a[1] * b[2] - a[2] * b[1],
      a[2] * b[0] - a[0] * b[2],
      a[0] * b[1] - a[1] * b[0],
    ];
    const [a, b, c, d] = definition.dihedral_indices.map(at);
    const axis = sub(c, b),
      length = norm(axis);
    const unit = axis.map((v) => v / length);
    const perpendicular = (v) => v.map((x, i) => x - dot(v, unit) * unit[i]);
    const v = perpendicular(sub(a, b)),
      w = perpendicular(sub(d, c));
    const angle =
      length > 1e-12 && norm(v) > 1e-12 && norm(w) > 1e-12
        ? ((Math.atan2(dot(cross(unit, v), w), dot(v, w)) * 180) / Math.PI +
            360) %
          360
        : null;
    const centers = definition.rings.map((ring) => {
      const mass = ring.reduce((s, i) => s + definition.masses[i], 0);
      return [0, 1, 2].map(
        (k) =>
          ring.reduce((s, i) => s + at(i)[k] * definition.masses[i], 0) / mass,
      );
    });
    return {
      dihedral_deg: angle,
      ring_distance_pm: norm(sub(centers[0], centers[1])) * 100,
    };
  },
  energyPoints(records) {
    const baseline = records[0]?.energy_ev || 0;
    return records.map((p) => ({
      x: p.step,
      y: p.energy_ev - baseline,
      energy: p.energy_ev,
      phase: p.phase,
    }));
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
    return {
      kind: "optimization",
      frames: records.length
        ? records.map((p) => p.positions)
        : molecule?.trajectory_kind === "vibration"
          ? []
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
