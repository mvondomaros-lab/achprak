"""Unit conversion helpers for notebook UI (bidirectional, observer-driven)."""

import IPython.display
import ipywidgets
import scipy.constants as const

STYLE = {"description_width": "120px"}
EPS = 1e-12


class EVNMConverter:
    """Bidirectional photon energy (eV) ↔ wavelength (nm)."""

    HC = const.Planck * const.c / const.electron_volt / const.nano

    @classmethod
    def ev_to_nm(cls, e_ev: float) -> float:
        return cls.HC / e_ev

    @classmethod
    def nm_to_ev(cls, wl_nm: float) -> float:
        return cls.HC / wl_nm

    def __init__(self):
        e0 = 3.5
        wl0 = self.ev_to_nm(e0)
        self._energy_eV = ipywidgets.FloatText(
            description="Energie / eV:",
            value=e0,
            step=0.0001,
            style=STYLE,
        )
        self._wavelength_nm = ipywidgets.FloatText(
            description="Wellenlänge / nm:",
            value=wl0,
            step=0.01,
            style=STYLE,
        )

        self._energy_eV.observe(self._on_change)
        self._wavelength_nm.observe(self._on_change)
        self._syncing = False

    def _on_change(self, change):
        if (
            change["type"] == "change"
            and change["name"] == "value"
            and not self._syncing
        ):
            self._syncing = True
            try:
                if change["owner"] == self._energy_eV:
                    if self._energy_eV.value is None or self._energy_eV.value <= 0:
                        return
                    with self._wavelength_nm.hold_trait_notifications():
                        new_wl = self.ev_to_nm(max(self._energy_eV.value, EPS))
                        self._wavelength_nm.value = round(new_wl, 2)
                elif change["owner"] == self._wavelength_nm:
                    if (
                        self._wavelength_nm.value is None
                        or self._wavelength_nm.value <= 0
                    ):
                        return
                    with self._energy_eV.hold_trait_notifications():
                        new_e = self.nm_to_ev(max(self._wavelength_nm.value, EPS))
                        self._energy_eV.value = round(new_e, 4)
            finally:
                self._syncing = False

    def show(self):
        """Display the converter widgets."""
        IPython.display.display(self._energy_eV, self._wavelength_nm)


class EVKJMolConverter:
    """Bidirectional energy conversion: eV ↔ kJ/mol."""

    EV_TO_KJMOL = const.electron_volt * const.N_A / 1000.0

    @classmethod
    def ev_to_kjmol(cls, e_ev: float) -> float:
        return e_ev * cls.EV_TO_KJMOL

    @classmethod
    def kjmol_to_ev(cls, e_kjmol: float) -> float:
        return e_kjmol / cls.EV_TO_KJMOL

    def __init__(self):
        e0 = 3.5
        self._energy_eV = ipywidgets.FloatText(
            description="Energie / eV:",
            value=e0,
            step=0.0001,
            style=STYLE,
        )
        kj0 = self.ev_to_kjmol(e0)
        self._energy_kJmol = ipywidgets.FloatText(
            description="Energie / kJ/mol:",
            value=round(kj0, 2),
            step=0.01,
            style=STYLE,
        )
        self._energy_eV.observe(self._on_change)
        self._energy_kJmol.observe(self._on_change)
        self._syncing = False

    def _on_change(self, change):
        if (
            change["type"] == "change"
            and change["name"] == "value"
            and not self._syncing
        ):
            self._syncing = True
            try:
                if change["owner"] == self._energy_eV:
                    if self._energy_eV.value is None:
                        return
                    with self._energy_kJmol.hold_trait_notifications():
                        new_kj = self.ev_to_kjmol(self._energy_eV.value)
                        self._energy_kJmol.value = round(new_kj, 2)
                elif change["owner"] == self._energy_kJmol:
                    if self._energy_kJmol.value is None:
                        return
                    with self._energy_eV.hold_trait_notifications():
                        new_ev = self.kjmol_to_ev(self._energy_kJmol.value)
                        self._energy_eV.value = round(new_ev, 6)
            finally:
                self._syncing = False

    def show(self):
        """Display the converter widgets."""
        IPython.display.display(self._energy_eV, self._energy_kJmol)
