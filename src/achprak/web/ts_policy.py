"""Course eligibility for web TS jobs; the research optimizer stays unrestricted."""

# Include historical groups so existing sessions retain their original TS limits.
SUBSTITUENTS = {"H", "Me", "OMe", "NMe2", "CF3", "CN", "NO2", "F", "SO2CF3"}
ORTHO_SITES = (0, 4, 5, 9)  # 2, 6, 2', 6'
MAX_TS_ATTEMPTS = 2


def ts_restriction(settings):
    """Return a student-facing reason, or None when the template is eligible."""
    values = settings.get("substituents") if isinstance(settings, dict) else None
    if (
        not isinstance(values, list)
        or len(values) != 10
        or any(not isinstance(v, str) or v not in SUBSTITUENTS for v in values)
    ):
        return (
            "Die Substitution dieser Struktur ist nicht mehr zugeordnet. "
            "Erstellen Sie die Startstruktur erneut und optimieren Sie ein Minimum, "
            "bevor Sie einen Übergangszustand suchen."
        )
    reasons = []
    if sum(v != "H" for v in values) > 2:
        reasons.append("höchstens zwei Substituenten insgesamt")
    if any(values[i] == "SO2CF3" for i in ORTHO_SITES):
        reasons.append("kein SO₂CF₃ an den Positionen 2, 6, 2′ oder 6′ (ortho)")
    if reasons:
        return (
            "Für die Übergangszustandssuche im Praktikum gilt: "
            + "; ".join(reasons)
            + ". Minimumsuche und Spektrenrechnung bleiben verfügbar."
        )
    return None


def molecule_settings(molecule, molecules):
    """Resolve provenance for existing sessions whose minima predate settings."""
    seen = set()
    while molecule is not None:
        if isinstance(molecule.get("settings"), dict):
            return molecule["settings"]
        parent = molecule.get("parent_id")
        if not parent or parent in seen:
            break
        seen.add(parent)
        molecule = molecules.get(parent)
    return None


def with_ts_policy(molecule, molecules):
    settings = molecule_settings(molecule, molecules)
    return dict(molecule, settings=settings, ts_restriction=ts_restriction(settings))
