# Transition-state calculation

TS searches require a converged minimum. A relaxed CNNC torsion scan seeds a
13-image path toward the opposite cis/trans isomer, preserving atom identity and
rotating the complete fragment. CNN angles are guided to 120° only during seed
preparation. The opposite endpoint is then freely minimized. Regular minimum
searches, opposite endpoints, and connectivity checks all use a final maximum
atomic force of 0.002 eV/Å and the same xTB accuracy setting (0.1).
ASE FIRE (L-BFGS on retry attempts) relaxes two unconstrained NEB halves against a provisionally refined central saddle seed.
This prevents early corner cutting from removing the barrier. The full band is
then released for climbing-image NEB. Both stages use 0.1 eV/Å² springs. Free Sella saddle
refinement follows, using a full Cartesian Hessian and a 0.005 eV/Å force threshold.
Candidates with additional imaginary modes are refined to 0.001 eV/Å within the
shared iteration budget, then their Hessian is recalculated. This resolves soft
torsions before mode validation. The central seed is approached in internal coordinates and finished in Cartesian coordinates;
final saddle refinement also uses Cartesian coordinates to handle nearly linear
CNN angles. Both endpoints and the band use GFN1-xTB with ALPB ethanol.
Minimum refinement uses internal-coordinate Sella followed by at most 25
Cartesian BFGS steps at the same force threshold. Each attempt shares a
1,500-iteration budget across its stages. Student searches
allow at most two attempts (3,000 steps total) and remain subject to the server's
wall-time limit. The retry uses reversed rotation at 120°, or an open 135°
seed for endpoint-preparation or changed-bond failures. The standalone API
uses the same two-attempt limit.

The live chart shows the evolving band's energy against normalized Cartesian
path length, not optimization time. The live 3D preview follows a moving image
of the active half-band, then the climbing image during CI-NEB. The plot highlights
the displayed image. On completion, clickable energy points and the
single-pass Play controls show the reaction path. Minimum results instead
show their optimization history.
Both endpoint geometries and their energies are retained
in the result; the other endpoint is available as the final path image.

A full all-atom finite-difference Hessian (0.01 Å displacement) checks the saddle.
Rigid translations and rotations are projected out; exactly one imaginary
internal frequency with magnitude above 20 cm⁻¹ is required. Smaller negative frequencies are tolerated by this numerical criterion;
they are not proof of additional physical instabilities. Displacement by ±0.15 Å maximum atom motion along the unstable
mode, followed by unconstrained minimization, must reach one cis and one trans
minimum with the original atom-mapped bond graph preserved. For this comparison,
copies of both band endpoints and the downhill minima are optimized to 0.002 eV/Å
to resolve soft torsions. Polishing takes place after the TS search and preserves
the original band and its energy reference. These actual downhill
minima (XYZ, energy, isomer) are retained separately. Matching to the polished
endpoint references additionally uses aligned RMSD <0.35 Å and energy difference <0.05 eV.
A different endpoint conformer is explicitly reported; isomer connectivity does
not establish an exact conformer match. This is a numerical downhill connectivity
check, **not an IRC** or a proof of the globally lowest barrier. Failed band, saddle,
mode or cis/trans connectivity checks leave an unconfirmed search state.
Only a force-converged saddle passing both mode and connectivity checks is labeled
a TS. Playback is not a dynamics simulation. Barriers are electronic energy differences, not free-energy
barriers. See [ASE's NEB documentation](https://docs.ase-lib.org/ase/neb.html).

