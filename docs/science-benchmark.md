# Scientific settings benchmark

## Scope

Local sensitivity study using the locked Pixi dev environment, one BLAS/OpenMP thread, ALPB ethanol geometries, xTB accuracy 0.1, and INDO/S–CIS with COSMO EPS=24.3. The initial embedding uses ETKDGv3 with seed 42 unless stated. The same optimization continues from 0.01 to 0.002 eV/Å. This measures the incremental cost of tightening, not two independent full runs. Timings are single runs on this machine and include concurrent benchmark/test load.

The push-pull case is trans-4-NMe2-4′-CF3 azobenzene; the sulfonyl case is trans-4-NMe2-4′-SO2CF3 azobenzene. Other substituent positions are given in the case names. All unspecified sites carry hydrogen.

This is not validation against experiment or higher-level reference chemistry. Method differences establish sensitivity, not which method is more accurate. Spectral peaks below refer to the strongest broadened maximum in 1.5–5.5 eV, with sigma 0.15 eV; peak identity can change when bands exchange intensity.

Reproduce with `pixi run -e dev python scripts/benchmark_science.py`, then `pixi run -e dev python scripts/benchmark_ts_methods.py`, and `pixi run -e dev python scripts/summarize_science_benchmark.py`. Set `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1` for comparable timings. Raw geometries, transition energies, oscillator strengths and logs are written under `results/science-benchmark/`. These expensive calculations are excluded from default tests.

## Geometry convergence

Energy change is E(loose) − E(tight). All rows retain the same molecular composition and method.

| Molecule | Method | Converged loose/tight | Steps loose + extra | Extra time / s | Energy change / kJ mol⁻¹ | Spectral peak change / eV |
|---|---|---|---:|---:|---:|---:|
| trans-H | GFN1-xTB | True/True | 13 + 2 | 0.073 | 0.0005 | +0.0000 |
| trans-H | GFN2-xTB | True/True | 11 + 1 | 0.033 | 0.0003 | +0.0000 |
| cis-H | GFN1-xTB | True/True | 10 + 3 | 0.112 | 0.0007 | +0.0000 |
| cis-H | GFN2-xTB | True/True | 9 + 4 | 0.152 | 0.0030 | +0.0000 |
| trans-2-Me | GFN1-xTB | True/True | 26 + 3 | 0.135 | 0.0005 | +0.0040 |
| trans-2-Me | GFN2-xTB | True/True | 19 + 2 | 0.081 | 0.0009 | +0.0000 |
| cis-2-Me | GFN1-xTB | True/True | 20 + 2 | 0.092 | 0.0004 | +0.0000 |
| cis-2-Me | GFN2-xTB | True/True | 22 + 2 | 0.083 | 0.0007 | +0.0000 |
| trans-4-NMe2 | GFN1-xTB | True/True | 12 + 17 | 1.000 | 0.1355 | -0.0280 |
| trans-4-NMe2 | GFN2-xTB | True/True | 12 + 6 | 0.318 | 0.0166 | -0.0040 |
| trans-push-pull | GFN1-xTB | True/True | 23 + 11 | 0.829 | 0.0098 | +0.0000 |
| trans-push-pull | GFN2-xTB | True/True | 17 + 13 | 0.852 | 0.0114 | -0.0080 |
| trans-push-pull-seed7 | GFN1-xTB | True/True | 22 + 7 | 0.501 | 0.0073 | +0.0040 |
| trans-push-pull-seed7 | GFN2-xTB | True/True | 21 + 10 | 0.659 | 0.0662 | -0.0120 |
| cis-2-OMe | GFN1-xTB | True/True | 13 + 2 | 0.095 | 0.0010 | +0.0000 |
| cis-2-OMe | GFN2-xTB | True/True | 14 + 3 | 0.124 | 0.0020 | +0.0000 |
| cis-2-OMe-seed7 | GFN1-xTB | True/True | 14 + 2 | 0.093 | 0.0003 | +0.0000 |
| cis-2-OMe-seed7 | GFN2-xTB | True/True | 17 + 2 | 0.084 | 0.0004 | +0.0000 |
| trans-sulfonyl | GFN1-xTB | True/True | 24 + 6 | 0.491 | 0.0038 | +0.0000 |
| trans-sulfonyl | GFN2-xTB | True/True | 14 + 8 | 0.606 | 0.0156 | +0.0000 |

## Configuration cutoff and output coverage

Shifts are 800 minus 2000 configurations at the same tight geometry. Both runs request WRTCI=200 (199 transitions in this MOPAC build). WRTCI=30 output contains 29 transitions. The plotted upper limit plus four Gaussian standard deviations is 6.1 eV.

| Molecule | Geometry method | First excitation shift / eV | Peak shift / eV | 800 / 2000 time / s | Last transition with WRTCI=30 / eV |
|---|---|---:|---:|---:|---:|
| trans-H | GFN1-xTB | +0.0028 | +0.0561 | 4.25 / 8.56 | 7.402 |
| trans-H | GFN2-xTB | +0.0036 | +0.0521 | 4.27 / 8.59 | 7.361 |
| cis-H | GFN1-xTB | +0.0037 | +0.0160 | 4.25 / 8.52 | 7.093 |
| cis-H | GFN2-xTB | +0.0039 | +0.0280 | 4.30 / 8.66 | 7.227 |
| trans-2-Me | GFN1-xTB | +0.0040 | +0.0801 | 4.76 / 14.53 | 7.230 |
| trans-2-Me | GFN2-xTB | +0.0060 | +0.0761 | 4.77 / 14.52 | 7.180 |
| cis-2-Me | GFN1-xTB | +0.0056 | -0.4164 | 4.73 / 14.57 | 7.055 |
| cis-2-Me | GFN2-xTB | +0.0059 | +0.0881 | 4.79 / 14.68 | 7.186 |
| trans-4-NMe2 | GFN1-xTB | +0.0054 | +0.0921 | 5.63 / 33.32 | 7.065 |
| trans-4-NMe2 | GFN2-xTB | +0.0061 | +0.0841 | 5.76 / 33.82 | 6.898 |
| trans-push-pull | GFN1-xTB | +0.0050 | +0.1001 | 7.12 / 56.85 | 6.812 |
| trans-push-pull | GFN2-xTB | +0.0111 | +0.0881 | 7.13 / 56.99 | 6.823 |
| trans-push-pull-seed7 | GFN1-xTB | +0.0047 | +0.0961 | 7.25 / 57.52 | 6.797 |
| trans-push-pull-seed7 | GFN2-xTB | +0.0105 | +0.0841 | 7.14 / 56.61 | 6.823 |
| cis-2-OMe | GFN1-xTB | +0.0056 | +0.0000 | 5.18 / 19.74 | 7.050 |
| cis-2-OMe | GFN2-xTB | +0.0071 | +0.0721 | 4.97 / 19.36 | 7.106 |
| cis-2-OMe-seed7 | GFN1-xTB | +0.0085 | +0.0000 | 4.98 / 19.40 | 7.075 |
| cis-2-OMe-seed7 | GFN2-xTB | +0.0075 | -1.6737 | 5.03 / 19.64 | 7.172 |
| trans-sulfonyl | GFN1-xTB | +0.0010 | +0.0440 | 8.27 / 63.42 | 6.358 |
| trans-sulfonyl | GFN2-xTB | +0.0112 | +0.0801 | 8.28 / 63.93 | 6.253 |

## Method sensitivity

Absolute total energies from different xTB methods must not be compared. Spectral peak changes below use the same INDO/S–CIS/800 method on the two optimized geometries.

| Molecule | GFN1 geometry peak / eV | GFN2 geometry peak / eV |
|---|---:|---:|
| trans-H | 3.4379 | 3.5420 |
| cis-H | 5.1276 | 5.2117 |
| trans-2-Me | 3.4219 | 3.6021 |
| cis-2-Me | 5.0836 | 5.1757 |
| trans-4-NMe2 | 2.8493 | 2.8934 |
| trans-push-pull | 2.8013 | 2.9935 |
| trans-push-pull-seed7 | 2.7893 | 2.9775 |
| cis-2-OMe | 5.5000 | 5.1196 |
| cis-2-OMe-seed7 | 5.5000 | 3.8263 |
| trans-sulfonyl | 2.8614 | 3.0816 |

The largest absolute energy change from evaluating the tight geometry with xTB accuracy 1.0 instead of 0.1 is 1.57e-07 eV. The app uses 0.1 for both geometry optimization and final energy reporting.

## Parent-isomer energy ordering

Differences are E(cis) − E(trans), each calculated within one method. They include the implicit-solvent model and omit nuclear thermal corrections.

- GFN1-xTB: +12.29 kJ/mol.
- GFN2-xTB: -6.54 kJ/mol.

## Alternative starting conformations

Seed 7 minus seed 42, within the same method and composition. Two seeds sample sensitivity; they do not establish a global minimum or an ensemble spectrum.

| Molecule | Method | Energy difference / kJ mol⁻¹ | Spectral peak difference / eV |
|---|---|---:|---:|
| trans-push-pull | GFN1-xTB | -0.1516 | -0.0120 |
| cis-2-OMe | GFN1-xTB | -0.7636 | +0.0000 |
| trans-push-pull | GFN2-xTB | -0.0239 | -0.0160 |
| cis-2-OMe | GFN2-xTB | +6.3326 | -1.2933 |

## Parent trans planarity

Unconstrained Cartesian BFGS refinement to 0.0001 eV/Å, including a second run starting from coordinates projected onto a plane. Ring twist measures the departure of an adjacent ring C–C–N–N torsion from 0° or 180°; CNNC alone does not measure phenyl-ring planarity. Full finite-difference Hessians use 0.01 Å displacement and rigid-mode projection. Reproduce with `pixi run -e dev python scripts/benchmark_planarity.py` before summarizing.

| Method | Planar seed | Converged | Ring twists / ° | Heavy-atom plane RMS / Å | Lowest internal frequency / cm⁻¹ |
|---|---|---|---:|---:|---:|
| GFN1-xTB | False | True | 0.20, 0.19 | 0.0015 | 30.69 |
| GFN1-xTB | True | True | 0.13, 0.26 | 0.0019 | 30.58 |
| GFN2-xTB | False | True | 17.71, 21.34 | 0.3384 | 35.67 |
| GFN2-xTB | True | True | 8.49, 10.00 | 0.0349 | 29.32 |

## GFN2-xTB transition-state checks

| Molecule | Confirmed TS | Time / s | Iterations | Barrier / eV | Failure |
|---|---|---:|---:|---:|---|
| cis-H | True | 27.9 | 700 | 0.6552339699939012 | — |
| trans-2-Me | True | 32.0 | 873 | 0.5757776912632835 | — |

## Recorded environment

```json
{
  "platform": "macOS-26.6.2-arm64-arm-64bit",
  "python": "3.12.13",
  "packages": {
    "numpy": "2.4.3",
    "ase": "3.28.0",
    "rdkit": "2026.3.1",
    "tblite": "0.5.0",
    "sella": "2.4.2",
    "pymopac": "1.1"
  },
  "mopac": "23.2.4",
  "threads": {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1"
  }
}
```
