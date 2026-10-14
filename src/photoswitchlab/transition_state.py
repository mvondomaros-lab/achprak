"""Two-endpoint CI-NEB search with saddle and downhill connectivity checks."""

import copy

import numpy as np
import sella
from ase import units
from ase.build import minimize_rotation_and_translation
from ase.constraints import FixInternals
from ase.mep import NEB
from ase.optimize import BFGS, FIRE, LBFGS
from ase.vibrations import Vibrations

from . import azobenzene, common


def internal_modes(atoms, hessian):
    """Mass-weighted modes with rigid translations and rotations projected out."""
    masses = atoms.get_masses()
    weights = np.repeat(masses**-0.5, 3)
    center = np.average(atoms.positions, axis=0, weights=masses)
    relative = atoms.positions - center
    rigid = []
    for axis in np.eye(3):
        rigid.append((np.ones_like(relative) * axis * np.sqrt(masses[:, None])).ravel())
        rigid.append((np.cross(relative, axis) * np.sqrt(masses[:, None])).ravel())
    u, singular, _ = np.linalg.svd(np.array(rigid).T, full_matrices=True)
    rank = np.count_nonzero(singular > singular[0] * 1e-10)
    basis = u[:, rank:]
    weighted = weights[:, None] * hessian * weights[None, :]
    eigenvalues, vectors = np.linalg.eigh(basis.T @ weighted @ basis)
    conversion = units._hbar * units.m / np.sqrt(units._e * units._amu) / units.invcm
    frequencies = np.sign(eigenvalues) * np.sqrt(np.abs(eigenvalues)) * conversion
    modes = ((basis @ vectors).T * weights).reshape(-1, len(atoms), 3)
    return frequencies, modes


class OptTS:
    """Connect optimized cis/trans endpoints using a torsion-seeded CI-NEB."""

    def __init__(self, atoms, calc=None):
        self.atoms = atoms.copy()
        properties = azobenzene.Properties(self.atoms)
        self.indices = properties.cnnc_dihedral_indices()
        # Rotate the entire fragment on one side of N=N, preserving all bonds.
        n1, n2 = self.indices[1:3]
        side, pending = {n2}, [n2]
        while pending:
            for neighbor in properties.mol.GetAtomWithIdx(pending.pop()).GetNeighbors():
                index = neighbor.GetIdx()
                if index != n1 and index not in side:
                    side.add(index)
                    pending.append(index)
        self.rotating_indices = sorted(side)
        self.calculator_factory = (
            (lambda: copy.deepcopy(calc))
            if calc is not None
            else lambda: common.DefaultASECalculator(
                accuracy=common.OPTIMIZATION_ACCURACY
            )
        )
        self.atoms.calc = self.calculator_factory()
        self.traj = []
        self.search_traj = []
        self.validation = None
        self.search_converged = False
        self.failure_reason = None
        self.barrier_ev = None
        self.iterations_used = 0

    def run(self, steps=1500, observer=None, *, max_attempts=2):
        """Try up to ``max_attempts`` deterministic seeds (at most two).

        Start with a 120° seed and FIRE. A crowded endpoint can relax back to
        the source isomer, while substituent conformations can stall one sense
        of rotation. Alternative seeds still require the full unconstrained
        saddle, frequency, and connectivity validation. Alternative attempts
        relax the band with L-BFGS to avoid repeating FIRE's stalled path.
        """
        if not isinstance(max_attempts, int) or not 1 <= max_attempts <= 2:
            raise ValueError("max_attempts must be an integer between 1 and 2")
        self.max_attempts = max_attempts
        source = self.atoms.copy()
        self.attempts = []
        self.step_limit_per_attempt = steps
        frames = []
        seeds = [(False, 120.0, 250)]
        index = 0
        while index < min(len(seeds), max_attempts):
            reverse, angle, downhill_steps = seeds[index]
            self.atoms = source.copy()
            offset = len(frames)

            def observe(frame, step, phase):
                frame.info["ts_attempt"] = index + 1
                if observer is not None:
                    observer(frame, offset + step, phase)

            ok = self._run_path(
                steps,
                observe,
                reverse=reverse,
                seed_angle=angle,
                downhill_steps=downhill_steps,
                use_lbfgs=index > 0,
            )
            self.attempts.append(
                {
                    "reverse_rotation": reverse,
                    "seed_angle_deg": angle,
                    "band_optimizer": "LBFGS" if index > 0 else "FIRE",
                    "iterations": self.iterations_used,
                    "converged": bool(ok),
                    "failure_reason": self.failure_reason,
                }
            )
            frames.extend(self.search_traj)
            if ok:
                break
            if index == 0:
                reversed_seed = (True, 120.0, 250)
                # A more open CNN geometry avoids crowded cis seeds. Use a
                # short downhill warmup before the internal-coordinate minimum
                # optimizer so soft substituent torsions do not use its budget.
                open_seed = (False, 135.0, 50)
                changed_bonds = self.connectivity is not None and any(
                    not branch["bonds_preserved"]
                    for branch in self.connectivity["branches"]
                )
                seeds.append(
                    open_seed
                    if self.endpoint is None or changed_bonds
                    else reversed_seed
                )
            index += 1
        self.iterations_used = sum(a["iterations"] for a in self.attempts)
        self.search_traj = frames
        self.traj = list(frames)
        return ok

    def _run_path(
        self,
        steps,
        observer,
        *,
        reverse=False,
        seed_angle=120.0,
        downhill_steps=250,
        use_lbfgs=False,
    ):
        self.traj, self.search_traj = [], []
        self.validation = self.failure_reason = self.barrier_ev = None
        self.search_converged = False
        self.iterations_used = 0
        self.path = []
        self.connectivity = None
        self.band_converged = False
        self.endpoint = None
        atoms = self.atoms
        initial = atoms.copy()
        initial.calc = self.calculator_factory()
        baseline = float(initial.get_potential_energy())
        if np.linalg.norm(initial.get_forces(), axis=1).max() > 0.03:
            raise ValueError(
                "Bitte vor der Übergangsstruktursuche eine Minimumstruktur suchen."
            )
        source_cis = np.cos(np.radians(initial.get_dihedral(*self.indices))) > 0

        def publish(frame, phase, band=None, image_index=None):
            frame.info.pop("neb_path", None)
            frame.info.pop("neb_image", None)
            if band is not None:
                frame.info["neb_image"] = image_index
                frame.info["neb_path"] = [
                    {k: v for k, v in p.items() if k != "positions"}
                    for p in self.path_records(band)
                ]
            self.search_traj.append(frame.copy())
            if observer is not None:
                observer(frame, len(self.search_traj) - 1, phase)

        def failed(reason):
            self.failure_reason = reason
            self.traj = list(self.search_traj)
            return False

        def optimize(optimizer, fmax, limit, callback=None):
            budget = max(0, min(limit, steps - self.iterations_used))
            with optimizer as opt:
                if callback is not None:
                    opt.attach(callback)
                ok = bool(opt.run(fmax=fmax, steps=budget))
                self.iterations_used += opt.nsteps
            return ok

        def optimize_minimum(frame, limit, callback):
            # Internal coordinates efficiently relax soft torsions; a Cartesian
            # finish resolves residual forces near linear groups such as CN.
            optimize(
                sella.Sella(frame, order=0, internal=True),
                common.MINIMUM_FMAX,
                limit,
                callback,
            )
            return optimize(
                BFGS(frame, logfile="-", maxstep=0.08),
                common.MINIMUM_FMAX,
                25,
                callback,
            )

        hessian_cache = None

        def band_optimizer(band):
            if use_lbfgs:
                return LBFGS(band, logfile="-", maxstep=0.05, use_line_search=False)
            return FIRE(band, logfile="-", dt=0.05, maxstep=0.05)

        def hessian(frame):
            # Sella 2.4+ accepts a Cartesian Hessian callback. Reuse the final
            # matrix for validation when the geometry has not changed.
            nonlocal hessian_cache
            if hessian_cache is None or not np.array_equal(
                frame.positions, hessian_cache[0]
            ):
                with common.tempdir():
                    vibrations = Vibrations(frame, delta=0.01)
                    vibrations.run()
                    matrix = vibrations.get_vibrations().get_hessian_2d()
                hessian_cache = (frame.positions.copy(), matrix)
            return hessian_cache[1]

        publish(initial, "endpoint")
        start = initial.get_dihedral(*self.indices)
        # Preserve atom identity and bonds by rotating the complete fragment.
        # A relaxed torsion path avoids Cartesian interpolation through N=N.
        target = 180.0 if source_cis else (0.0 if start < 180 else 360.0)
        images = [initial]
        quarter = 90.0 if start < 180 else 270.0
        if reverse:
            if source_cis:
                quarter = -90.0 if start < 180 else 450.0
                target = -180.0 if start < 180 else 540.0
            else:
                quarter = 270.0 if start < 180 else 90.0
                target = 360.0 if start < 180 else 0.0
        angles = np.r_[
            np.linspace(start, quarter, 7)[1:], np.linspace(quarter, target, 7)[1:]
        ]
        for angle in angles:
            frame = images[-1].copy()
            frame.calc = self.calculator_factory()
            frame.set_dihedral(
                *self.indices, float(angle), indices=self.rotating_indices
            )
            frame.set_constraint(
                FixInternals(
                    dihedrals_deg=[[float(angle), self.indices]],
                    angles_deg=[
                        [seed_angle, self.indices[:3]],
                        [seed_angle, self.indices[1:]],
                    ],
                )
            )
            try:
                frame.set_positions(frame.positions)
                relaxed = optimize(BFGS(frame, logfile="-", maxstep=0.1), 0.05, 160)
            finally:
                frame.set_constraint()
            publish(frame, "path_seed")
            self.atoms = frame
            if not relaxed:
                return failed(
                    "Der Reaktionspfad ist nach der Vorbereitung noch nicht ausreichend optimiert."
                )
            images.append(frame)
        endpoint = images[-1]
        if not optimize_minimum(
            endpoint,
            200,
            lambda: publish(endpoint, "endpoint"),
        ):
            return failed(
                "Die Minimumsuche für das andere Isomer ist nicht abgeschlossen."
            )
        endpoint_cis = np.cos(np.radians(endpoint.get_dihedral(*self.indices))) > 0
        if endpoint_cis == source_cis:
            return failed(
                "Die Minimumsuche hat wieder das Ausgangsisomer statt des anderen Isomers erreicht."
            )
        self.endpoint = endpoint.copy()
        self.endpoint.calc = self.calculator_factory()
        # All path constraints have now been removed; endpoints remain fixed.
        # Strong springs (1 eV/Å²) stall the methyl-substituted half-path.
        # Use the same softer springs during half-band and climbing relaxation.
        spring_constant = 0.1  # eV/Å²
        band = NEB(
            images,
            k=spring_constant,
            climb=False,
            method="improvedtangent",
            remove_rotation_and_translation=True,
        )

        def band_progress(preview_index=None):
            peak_index = max(
                range(1, len(images) - 1),
                key=lambda i: images[i].get_potential_energy(),
            )
            self.atoms = images[peak_index]
            self.path = self.path_records(images)
            # The saddle is fixed during half-band relaxation. Preview a
            # mobile image there; follow the climbing image once released.
            index = peak_index if preview_index is None else preview_index
            publish(
                images[index],
                "neb_climb" if band.climb else "neb",
                images,
                image_index=index,
            )

        # Refine the central rotational seed before band relaxation so
        # early corner cutting does not remove the barrier from the band.
        self.path = self.path_records(images)
        center = images[6]
        self.atoms = center
        # Internal coordinates efficiently approach the rotational saddle.
        # Finish in Cartesian coordinates: near-linear CNN angles can make
        # the internal-coordinate force criterion misleading.
        optimize(
            sella.Sella(center, order=1, internal=True),
            0.02,
            100,
            lambda: publish(center, "refinement"),
        )
        if not optimize(
            sella.Sella(center, order=1, internal=False, hessian_function=hessian),
            0.005,
            150,
            lambda: publish(center, "refinement"),
        ):
            return failed(
                "Die Verfeinerung des Kandidaten für die Übergangsstruktur ist nicht abgeschlossen."
            )
        # Relax both halves against the central seed before letting it climb.
        # This aligns the local band tangent with the saddle's downhill paths.
        for half, preview_index in ((images[:7], 3), (images[6:], 9)):
            approach = NEB(
                half,
                k=spring_constant,
                climb=False,
                method="improvedtangent",
                remove_rotation_and_translation=True,
            )
            if not optimize(
                band_optimizer(approach),
                0.05,
                400,
                lambda index=preview_index: band_progress(index),
            ):
                return failed(
                    "Ein Teil des Reaktionspfads zur Übergangsstruktur ist noch nicht ausreichend optimiert."
                )
        band.climb = True
        if not optimize(band_optimizer(band), 0.05, 600, band_progress):
            return failed(
                "Die Kräfte am Reaktionspfad wurden innerhalb des Schrittlimits nicht ausreichend klein."
            )
        self.band_converged = True
        peak_index = int(np.argmax([a.get_potential_energy() for a in images]))
        if peak_index in (0, len(images) - 1):
            return failed("Der Verbindungspfad besitzt keine innere Energiebarriere.")
        atoms = images[peak_index].copy()
        atoms.calc = self.calculator_factory()
        self.atoms = atoms

        def refine_saddle(fmax):
            return optimize(
                sella.Sella(atoms, order=1, internal=False, hessian_function=hessian),
                fmax,
                150,
                lambda: publish(atoms, "refinement"),
            )

        self.search_converged = refine_saddle(0.005)
        if not self.search_converged:
            return failed(
                "Die abschließende Verfeinerung der Übergangsstruktur ist nicht abgeschlossen."
            )
        publish(atoms, "vibrations")
        frequencies, modes = internal_modes(atoms, hessian(atoms))
        negative = np.flatnonzero(frequencies < -20.0)
        # A loose force threshold can leave soft torsions unresolved: cis-2-Me
        # retains a second imaginary mode near -26 cm⁻¹. Polish such candidates
        # within the shared budget, then recompute all modes at the new geometry.
        if len(negative) > 1:
            self.search_converged = refine_saddle(0.001)
            if not self.search_converged:
                return failed(
                    "Die zusätzliche Verfeinerung der Übergangsstruktur ist nicht abgeschlossen."
                )
            publish(atoms, "vibrations")
            frequencies, modes = internal_modes(atoms, hessian(atoms))
            negative = np.flatnonzero(frequencies < -20.0)
        self.barrier_ev = float(atoms.get_potential_energy()) - baseline
        if atoms.get_potential_energy() <= max(
            baseline, endpoint.get_potential_energy()
        ):
            return failed(
                "Die Energie des Kandidaten liegt nicht oberhalb der Energien beider Minimumstrukturen."
            )
        self.validation = {
            "scope": "all_atoms",
            "rigid_modes_projected_out": True,
            "imaginary_threshold_cm1": 20.0,
            "frequencies_cm1": frequencies.tolist(),
            "imaginary_count": len(negative),
            "verified": len(negative) == 1,
        }
        if len(negative) != 1:
            return failed(
                f"Keine bestätigte Übergangsstruktur: {len(negative)} imaginäre Frequenzen mit einem Betrag über 20 cm⁻¹."
            )
        mode = modes[int(negative[0])].copy()
        mode /= np.linalg.norm(mode, axis=1).max()
        self.validation["imaginary_frequency_cm1"] = float(
            abs(frequencies[negative[0]])
        )
        # Follow both signs of the unstable mode by unconstrained downhill
        # optimization. This is a connectivity check, not a mass-weighted IRC.
        # Polish reference copies only after the TS search, preserving the
        # band geometry and its energy reference. Loose forces can leave soft
        # torsions far apart even within the same minimum's basin.
        references = [initial.copy(), endpoint.copy()]
        for reference in references:
            reference.calc = self.calculator_factory()
            if not optimize_minimum(
                reference,
                100,
                lambda: publish(reference, "connectivity"),
            ):
                return failed(
                    "Ein Vergleichsminimum ist noch nicht ausreichend optimiert, um die räumlichen Anordnungen zu vergleichen."
                )
        source_bonds = self.bond_graph(initial)
        branches = []
        for sign in (-1, 1):
            downhill = atoms.copy()
            downhill.calc = self.calculator_factory()
            downhill.positions += sign * 0.15 * mode
            # Descend from the unstable mode, then tighten to the same final
            # force tolerance as a normal minimum job, in Cartesian coordinates.
            optimize(
                BFGS(downhill, logfile="-", maxstep=0.08),
                0.02,
                downhill_steps,
                lambda: publish(downhill, "connectivity"),
            )
            ok = optimize_minimum(
                downhill,
                150,
                lambda: publish(downhill, "connectivity"),
            )
            matches = []
            for end in references:
                aligned = downhill.copy()
                minimize_rotation_and_translation(end, aligned)
                rmsd = float(
                    np.sqrt(
                        np.mean(
                            np.sum((aligned.positions - end.positions) ** 2, axis=1)
                        )
                    )
                )
                delta = abs(
                    float(downhill.get_potential_energy() - end.get_potential_energy())
                )
                matches.append(
                    {
                        "rmsd_angstrom": rmsd,
                        "energy_difference_ev": delta,
                        "matches": bool(
                            ok
                            and rmsd < 0.35
                            and delta < 0.05
                            and (
                                np.cos(np.radians(downhill.get_dihedral(*self.indices)))
                                > 0
                            )
                            == (np.cos(np.radians(end.get_dihedral(*self.indices))) > 0)
                        ),
                    }
                )
            isomer = (
                "cis"
                if np.cos(np.radians(downhill.get_dihedral(*self.indices))) > 0
                else "trans"
            )
            branches.append(
                {
                    "converged": ok,
                    "matches": matches,
                    "isomer": isomer,
                    "xyz": common.atoms_to_xyz(downhill),
                    "energy_ev": float(downhill.get_potential_energy()),
                    "bonds_preserved": self.bond_graph(downhill) == source_bonds,
                }
            )
        exact_endpoints = (
            branches[0]["matches"][0]["matches"]
            and branches[1]["matches"][1]["matches"]
        ) or (
            branches[0]["matches"][1]["matches"]
            and branches[1]["matches"][0]["matches"]
        )
        connected = all(b["converged"] and b["bonds_preserved"] for b in branches) and {
            b["isomer"] for b in branches
        } == {"cis", "trans"}
        self.connectivity = {
            "method": "unstable_mode_displacement_and_downhill_optimization",
            "verified": bool(connected),
            "scope": "cis_trans_isomers",
            "minimum_fmax_ev_angstrom": common.MINIMUM_FMAX,
            "reference_minima": [
                {
                    "xyz": common.atoms_to_xyz(r),
                    "energy_ev": float(r.get_potential_energy()),
                }
                for r in references
            ],
            "endpoint_conformers_match": bool(exact_endpoints),
            "branches": branches,
            "rmsd_tolerance_angstrom": 0.35,
            "energy_tolerance_ev": 0.05,
        }
        publish(atoms, "complete")
        if not connected:
            return failed(
                "Ein Sattelpunkt wurde gefunden, aber die Verbindung zu cis- und trans-Minimumstrukturen ist nicht bestätigt."
            )
        images[peak_index] = atoms
        self.path = self.path_records(images)
        return True

    @staticmethod
    def path_records(images):
        distances = [0.0]
        for previous, image in zip(images, images[1:]):
            distances.append(
                distances[-1]
                + float(np.linalg.norm(image.positions - previous.positions))
            )
        length = distances[-1] or 1.0
        return [
            {
                "image": i,
                "coordinate": distances[i] / length,
                "positions": image.positions.round(6).reshape(-1).tolist(),
                "energy_ev": float(image.get_potential_energy()),
            }
            for i, image in enumerate(images)
        ]

    @staticmethod
    def bond_graph(atoms):
        return {
            (
                min(b.GetBeginAtomIdx(), b.GetEndAtomIdx()),
                max(b.GetBeginAtomIdx(), b.GetEndAtomIdx()),
                b.GetBondTypeAsDouble(),
            )
            for b in azobenzene.Properties(atoms.copy()).mol.GetBonds()
        }
