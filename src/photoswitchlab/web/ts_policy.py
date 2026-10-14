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
            "Erstellen Sie die Startstruktur erneut und suchen Sie eine Minimumstruktur, "
            "bevor Sie eine Übergangsstruktur suchen."
        )
    if sum(v != "H" for v in values) > 2:
        return (
            "Für die Übergangsstruktursuche im Praktikum sind höchstens zwei "
            "Substituenten insgesamt erlaubt. "
            "Minimumsuche und Spektrenrechnung bleiben verfügbar."
        )
    return None


def with_ts_policy(molecule):
    return dict(molecule, ts_restriction=ts_restriction(molecule.get("settings")))
