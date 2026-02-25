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
