"""The position selectors define an arrangement, not only connectivity."""

import numpy as np
import pytest
from rdkit import Chem
from rdkit.Chem import rdMolTransforms

from achprak.azobenzene import Template
from achprak.conformation import draw_coordinates, scaffold


@pytest.mark.parametrize("configuration", ["cis", "trans"])
@pytest.mark.parametrize("substitutions", [
    {},
    {"r1c1": "NO2", "r2c1": "CN"},
    {"r1c1": "NO2", "r2c5": "CN"},
    {"r1c3": "NMe2", "r2c3": "NO2"},
    {"r1c1": "OMe", "r1c5": "OMe", "r2c1": "OMe", "r2c5": "OMe"},
])
def test_drawing_and_start_share_ring_orientation(configuration, substitutions):
    template = Template(configuration=configuration, **substitutions)
    flat = Chem.RemoveHs(Chem.Mol(template.molh))
    draw_coordinates(flat)
    _, indices = scaffold(flat)
    for core_torsion, tolerance in [((5, 6, 7, 8), 25), ((7, 6, 5, 0), 50), ((6, 7, 8, 9), 50)]:
        torsion = [indices[i] for i in core_torsion]
        a = rdMolTransforms.GetDihedralDeg(flat.GetConformer(), *torsion)
        b = rdMolTransforms.GetDihedralDeg(template.molh.GetConformer(), *torsion)
        assert abs((b - a + 180) % 360 - 180) < tolerance
    distances = template.atoms.get_all_distances()
    np.fill_diagonal(distances, np.inf)
    assert distances.min() > 0.6  # No near-coincident atoms after preparation.
    assert not template.atoms.constraints  # Subsequent xTB relaxation is unrestricted.


def test_equivalent_ortho_sites_construct_distinct_starting_arrangements():
    starts = [Template(r1c1="NO2", **{position: "CN"}) for position in ("r2c1", "r2c5")]
    assert Chem.MolToSmiles(starts[0].mol) == Chem.MolToSmiles(starts[1].mol)
    angles = []
    for template in starts:
        _, indices = scaffold(template.molh)
        ring_carbon = template.molh.GetSubstructMatch(Chem.MolFromSmarts("c-C#N"))[0]
        angles.append(rdMolTransforms.GetDihedralDeg(
            template.molh.GetConformer(), indices[6], indices[7], indices[8], ring_carbon))
    assert abs((angles[1] - angles[0] + 180) % 360 - 180) > 90
