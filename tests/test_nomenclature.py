import pytest

from achprak.nomenclature import azobenzene_name, canonical_substitution


def substitutions(**positions):
    values = ["H"] * 10
    for position, substituent in positions.items():
        ring, locant = position.split("_")
        values[(int(ring[1]) - 1) * 5 + int(locant) - 2] = substituent
    return values


@pytest.mark.parametrize(
    "configuration, expected",
    [("trans", "(E)-Azobenzol"), ("cis", "(Z)-Azobenzol")],
)
def test_unsubstituted_names_use_stereodescriptors(configuration, expected):
    assert azobenzene_name(configuration, ["H"] * 10) == expected


def test_single_substituent_gets_the_lowest_ring_locant():
    values = substitutions(r1_6="OMe")
    assert azobenzene_name("trans", values) == "(E)-2-Methoxyazobenzol"
    assert canonical_substitution(values)[0][0] == "OMe"


def test_equivalent_rings_receive_the_same_name():
    assert azobenzene_name("cis", substitutions(r2_5="NO2")) == "(Z)-3-Nitroazobenzol"
    assert azobenzene_name("cis", substitutions(r1_3="NO2")) == "(Z)-3-Nitroazobenzol"


def test_repeated_substituents_use_multiplicative_prefixes_and_primes():
    values = substitutions(r1_6="OMe", r2_6="OMe")
    assert azobenzene_name("trans", values) == "(E)-2,2′-Dimethoxyazobenzol"


def test_alphabetical_precedence_breaks_equal_locant_ties():
    values = substitutions(r1_2="NO2", r1_6="OMe")
    assert azobenzene_name("trans", values) == "(E)-2-Methoxy-6-Nitroazobenzol"


def test_supported_substituents_have_german_names_in_alphabetical_order():
    values = substitutions(r1_2="NO2", r1_3="CN", r1_4="CF3", r2_2="Me", r2_3="NMe2")
    assert azobenzene_name("cis", values) == (
        "(Z)-3-Cyano-3′-Dimethylamino-2′-Methyl-2-Nitro-4-Trifluormethylazobenzol"
    )
