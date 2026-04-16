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

import matplotlib.pyplot as plt

from . import azobenzene
from . import conversion
from . import optimization
from . import uvvis

import warnings

# Set plotting style.
plt.style.use("ggplot")

# Ignore the warning about log flushes, which is not relevant for this package.
warnings.filterwarnings(
    "ignore",
    message="Log flushes by default now",
    category=FutureWarning,
)
