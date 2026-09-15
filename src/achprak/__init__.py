# The sella/ase/tblite stack does not parallelize well for these systems.
# Force serial execution before importing achprak or any dependency that may
# initialize BLAS/OpenMP runtimes.

import os

for var in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(var, "1")
