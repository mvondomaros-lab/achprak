from . import azobenzene
from . import optimization
from . import uvvis

# Set plotting style.
import matplotlib.pyplot as plt

plt.style.use("ggplot")

# Disables a UserWarning.
from pyscf import __config__

__config__.B3LYP_WITH_VWN5 = False
