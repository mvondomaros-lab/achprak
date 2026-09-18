"""Names for the deliberately limited azobenzene template library."""

from itertools import product

SUBSTITUENT_NAMES = {
    "Me": "Methyl",
    "OMe": "Methoxy",
    "NMe2": "Dimethylamino",
    "CF3": "Trifluormethyl",
    "CN": "Cyano",
    "NO2": "Nitro",
}

MULTIPLICATIVE_PREFIXES = {
    2: "Di",
    3: "Tri",
    4: "Tetra",
    5: "Penta",
    6: "Hexa",
    7: "Hepta",
    8: "Octa",
    9: "Nona",
    10: "Deca",
}


def _orientations(substituents):
    rings = (tuple(substituents[:5]), tuple(substituents[5:]))
    for swap, reverse_first, reverse_second in product((False, True), repeat=3):
        first, second = rings[::-1] if swap else rings
        if reverse_first:
            first = first[::-1]
        if reverse_second:
            second = second[::-1]
        yield first, second


def _locants(rings):
    result = {substituent: [] for substituent in SUBSTITUENT_NAMES}
    for primed, ring in enumerate(rings):
        for position, substituent in enumerate(ring, start=2):
            if substituent != "H":
                result[substituent].append((position, primed))
    return {key: value for key, value in result.items() if value}


def _orientation_key(rings):
    """Apply lowest-locant rules, then the alphabetical tie-breaker."""
    locants = _locants(rings)
    all_numbers = tuple(
        sorted(position for values in locants.values() for position, _ in values)
    )
    alphabetical = tuple(
        tuple(sorted(locants[substituent]))
        for substituent in sorted(
            locants, key=lambda item: SUBSTITUENT_NAMES[item].casefold()
        )
    )
    return all_numbers, alphabetical


def canonical_substitution(substituents):
    """Return the canonically numbered pair of five-member substitution lists."""
    if len(substituents) != 10:
        raise ValueError("Für ein Azobenzol werden zehn Ringpositionen erwartet.")
    unknown = set(substituents) - {"H", *SUBSTITUENT_NAMES}
    if unknown:
        raise ValueError(f"Unbekannte Substituenten: {', '.join(sorted(unknown))}")
    return min(_orientations(substituents), key=_orientation_key)


def azobenzene_name(configuration, substituents):
    """Return a canonical German retained name such as ``trans-2-Methoxyazobenzol``."""
    if configuration not in {"trans", "cis"}:
        raise ValueError(f"Unbekannte Konfiguration: {configuration}")

    locants = _locants(canonical_substitution(substituents))
    parts = []
    for substituent in sorted(
        locants, key=lambda item: SUBSTITUENT_NAMES[item].casefold()
    ):
        positions = sorted(locants[substituent])
        locant_text = ",".join(
            f"{position}{'′' if primed else ''}" for position, primed in positions
        )
        prefix = MULTIPLICATIVE_PREFIXES.get(len(positions), "")
        name = SUBSTITUENT_NAMES[substituent]
        if prefix:
            name = prefix + name[0].lower() + name[1:]
        parts.append(f"{locant_text}-{name}")
    substitution = "-".join(parts)
    parent = "azobenzol" if substitution else "Azobenzol"
    return f"{configuration}-{substitution}{parent}"
