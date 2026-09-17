# Transition-structure calculation

The application searches for a transition structure (TS) connecting cis and trans
minima on the chosen electronic energy surface. It requires a converged source
minimum structure and permits at most two non-H substituents across both rings. The
[scientific defaults](science-decisions.md) describe the energy and solvent model.

The interface calls the calculated saddle-point geometry a **transition structure**:
a geometry at which the energy decreases along one internal motion and increases
along the other internal directions. The fundamentals distinguish this geometry
from the statistical concept of a **transition state** in rate theory.

## What an accepted result establishes

A result is labeled as a TS only when all three checks pass:

1. The saddle-point geometry meets the force-convergence criterion.
2. Its vibrational analysis has exactly one imaginary internal frequency with
   magnitude above **20 cm⁻¹** (inverse centimetres). This identifies one
   direction of negative energy curvature. Smaller imaginary frequencies are
   tolerated by the numerical criterion; they are not classified as additional
   physical instabilities by this check.
3. Small displacements in the two directions of the unstable motion, followed
   by minimization, reach one cis and one trans minimum structure without changing the
   molecule's atom identities and bond connectivity.

This is a numerical downhill connectivity check. It is not an **intrinsic reaction
coordinate (IRC)** calculation, which follows a defined steepest-descent path in
mass-weighted coordinates. Nor does it establish that the search found the
globally lowest electronic energy barrier or the experimentally dominant reaction
pathway. A failed check leaves the search unconfirmed.

The reported **electronic energy barrier ΔE‡** is relative to the source minimum structure.
It excludes zero-point, thermal and entropic corrections and is neither an
Arrhenius activation energy nor a Gibbs energy of activation.

## Search sequence

The search first prepares an approximate path between the isomers. It then relaxes
a sequence of molecular geometries along that path and refines a candidate saddle
point. The geometries along the path are called **images**; they are not frames
sampled from a dynamics simulation.

The path method is the **nudged elastic band (NEB)** method. Artificial springs
maintain the spacing between images while the geometries relax. A climbing-image
stage drives the highest-energy image toward a saddle point. The [ASE
documentation](https://docs.ase-lib.org/ase/neb.html) describes this method; ASE
is the Atomic Simulation Environment used to organize these calculations. Sella
then refines the transition structure without the path springs.

Each attempt has a shared budget of 1,500 optimizer iterations. The application
and standalone calculation API permit at most two attempts. The server's
wall-clock time limit can end a search before that budget is exhausted.

<details>
<summary>Path preparation and optimizer settings</summary>

A relaxed scan of the C–N=N–C torsion prepares a 13-image path toward the opposite
isomer. Complete molecular fragments are rotated with atom identities preserved.
The C–N=N bond angles are guided to 120° only during preparation; the opposite
endpoint is then minimized without those constraints.

Two NEB halves initially relax against a provisionally refined central saddle
candidate. This staging reduces the risk that the initial path relaxes away from
the barrier region. The full band is then released for climbing-image NEB. Both
stages use a spring constant of 0.1 eV/Å². The first attempt uses FIRE, an
optimization algorithm based on damped motion. Retry attempts use L-BFGS, an
algorithm that estimates energy curvature from recent optimization steps.

The central candidate is approached using internal coordinates (bond lengths,
angles and torsions) and finished using Cartesian atomic coordinates. Final Sella
saddle refinement also uses Cartesian coordinates to handle nearly linear C–N=N
angles. It uses a full Cartesian Hessian, the matrix of second derivatives of the
energy, and a force threshold of 0.005 eV/Å. If additional imaginary modes remain,
refinement continues to 0.001 eV/Å within the shared iteration budget, then the
Hessian is recalculated.

Ordinary minimum structures, opposite endpoints and downhill checks use a largest-force
threshold of 0.002 eV/Å. Here eV denotes electronvolts and Å ångströms. Minimum
refinement uses internal-coordinate Sella followed by at most 25 Cartesian BFGS
steps at the same threshold. All use GFN1-xTB with ALPB ethanol and xTB numerical
accuracy 0.1.

The retry reverses the rotation with a 120° preparation angle, or uses a wider
135° angle after endpoint-preparation or changed-bond failures. These are
alternative initial guesses, not restraints on the accepted transition structure.

</details>

<details>
<summary>Frequency and endpoint-matching settings</summary>

A full all-atom Hessian is calculated by finite differences using displacements of
0.01 Å. Overall translation and rotation are projected out before interpreting the
internal frequencies.

The unstable mode is scaled so that its largest atomic displacement is 0.15 Å.
Minimization is started from both signs of that displacement. Copies of the band
endpoints and the resulting downhill minimum structures are refined to 0.002 eV/Å before
comparison, to resolve soft torsions. This extra refinement preserves the original
band and its energy reference.

Matching an endpoint requires an aligned root-mean-square atomic displacement
(RMSD) below 0.35 Å and an energy difference below 0.05 eV. A different endpoint
conformer is reported explicitly: reaching the correct isomer does not establish
an exact conformer match. Downhill geometries, energies and isomer assignments are
retained separately from the original path endpoints.

</details>

## Reading the path and playback

During the search, the chart plots image energies against normalized Cartesian
path length: cumulative displacement along the sequence, rescaled to its total
length. The horizontal axis is not elapsed time. The preview shows a moving image
of the active half-band, then the climbing image, and highlights its point on the
chart.

After completion, selecting an energy point or playing the sequence displays the
reaction path once. Both endpoint geometries and energies are retained; the
opposite endpoint is the final path image. Minimum results instead show the
history of geometry optimization. Neither playback is molecular dynamics or a
prediction of how rapidly the molecule moves.
