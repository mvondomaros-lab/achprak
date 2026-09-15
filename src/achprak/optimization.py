import tempfile

import ase.io
import sella

from . import common


class OptMin:
    """
    Geometry optimization.
    """

    def __init__(self, atoms, calc=None):
        self.atoms = atoms
        self.atoms.calc = calc or common.DefaultASECalculator(
            accuracy=common.OPTIMIZATION_ACCURACY
        )
        self.traj = None

    def run(self, steps=500, observer=None):
        """
        Perform a geometry optimization.
        """
        with tempfile.NamedTemporaryFile(suffix=".traj") as tmp:
            opt = sella.Sella(self.atoms, order=0, internal=True, trajectory=tmp.name)
            if observer is not None:
                opt.attach(lambda: observer(self.atoms, opt.nsteps, "optimization"))
            converged = opt.run(fmax=common.MINIMUM_FMAX, steps=steps)
            self.traj = ase.io.read(tmp.name, index=":")
        return converged
