"""Course-menu consistency and chemical connectivity of the new acceptors."""

import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

from achprak.azobenzene import Template
from achprak import common
from achprak.web.server import Settings, SUBSTITUENTS
from achprak.web.ts_policy import ts_restriction


def test_course_menu_is_consistent():
    expected = ["H", "Me", "OMe", "NMe2", "CF3", "CN", "NO2"]
    assert list(Template.substituent_smiles) == SUBSTITUENTS == expected
    app = (Path(__file__).parents[1] / "src/achprak/web/static/app.js").read_text()
    assert re.search(r"const SUBS = (.*);", app)[1] == str(expected).replace("'", '"')
    for group in expected:
        values = [group] + ["H"] * 9
        assert Settings(substituents=values).substituents == values
        assert ts_restriction({"substituents": values}) is None
    for group in ["F", "SO2CF3"]:
        with pytest.raises(ValidationError):
            Settings(substituents=[group] + ["H"] * 9)


@pytest.mark.parametrize("configuration", ["cis", "trans"])
@pytest.mark.parametrize("group,formula,pattern", [
    ("CN", "C13H9N3", "c-C#N"),
    ("NO2", "C12H9N3O2", "c-[N+](=O)[O-]"),
])
def test_acceptor_structure(configuration, group, formula, pattern):
    template = Template(configuration=configuration, r1c3=group)
    assert rdMolDescriptors.CalcMolFormula(template.mol) == formula
    assert Chem.GetFormalCharge(template.mol) == 0
    assert template.mol.HasSubstructMatch(Chem.MolFromSmarts(pattern))
    perceived = common.atoms_to_mol(template.atoms)
    assert rdMolDescriptors.CalcMolFormula(perceived) == formula
    assert perceived.HasSubstructMatch(Chem.MolFromSmarts(pattern))
    azo = [b for b in template.mol.GetBonds()
           if b.GetBeginAtom().GetSymbol() == b.GetEndAtom().GetSymbol() == "N"]
    assert len(azo) == 1
    assert azo[0].GetStereo() == (Chem.BondStereo.STEREOE if configuration == "trans" else Chem.BondStereo.STEREOZ)
