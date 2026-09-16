"""Course eligibility for web TS jobs."""

SUBSTITUENTS = {"H", "Me", "OMe", "NMe2", "CF3", "CN", "NO2"}
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
    if sum(v != "H" for v in values) > 2:
        return (
            "Für die Übergangszustandssuche im Praktikum sind höchstens zwei "
            "Substituenten insgesamt erlaubt. "
            "Minimumsuche und Spektrenrechnung bleiben verfügbar."
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
