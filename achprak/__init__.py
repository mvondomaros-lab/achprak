import matplotlib.pyplot as plt
import pyscf

from . import azobenzene
from . import optimization
from . import uvvis

# Set plotting style.
plt.style.use("ggplot")

# Disables a UserWarning.
pyscf.__config__.B3LYP_WITH_VWN5 = False
