"""Check symmetry reduction against molecular graphs without 3D calculations."""

import importlib.util
from pathlib import Path

from rdkit import Chem

from achprak.azobenzene import Template

spec = importlib.util.spec_from_file_location(
    "screen_ts", Path(__file__).resolve().parents[1] / "scripts/screen_ts.py"
)
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


def test_symmetry_orbits_match_canonical_stereochemical_graphs(tmp_path):
    raw = list(screen.cases("both-rings"))
    assert {s for case in raw for s in case["substituents"]} == set(
        Template.substituent_smiles
    )
    by_key, by_smiles = {}, {}
    for case in raw:
        # Only construct the molecular graph, avoiding embedding/optimization.
        template = object.__new__(Template)
        template.configuration = case["configuration"]
        template.substituents = case["substituents"]
        smiles = Chem.MolToSmiles(
            Chem.MolFromSmiles(template._init_smiles()), isomericSmiles=True
        )
        key = screen.symmetry_key(case)
        assert by_key.setdefault(key, smiles) == smiles
        assert by_smiles.setdefault(smiles, key) == key
    unique = screen.unique_cases(raw, tmp_path)
    assert len(unique) == len(by_smiles) == 750
    assert sum(c["substituents"].count("H") == 9 for c in unique) == 36
    assert (
        sum(
            any(s != "H" for s in c["substituents"][:5])
            and any(s != "H" for s in c["substituents"][5:])
            for c in unique
        )
        == 342
    )
    assert sum(len(c["equivalent_ids"]) for c in unique) == len(raw) == 3300


def test_existing_representative_is_reused_without_relabeling(tmp_path):
    raw = list(screen.cases("mono"))
    group = screen.unique_cases(raw, tmp_path)[0]
    existing = next(c for c in raw if c["id"] == group["equivalent_ids"][-1])
    (tmp_path / (existing["id"] + ".json")).write_text("{}")
    reused = next(
        c
        for c in screen.unique_cases(raw, tmp_path)
        if screen.symmetry_key(c) == screen.symmetry_key(existing)
    )
    assert reused["id"] == existing["id"]
    assert reused["substituents"] == existing["substituents"]
