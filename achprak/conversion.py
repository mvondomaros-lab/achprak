import IPython.display
import ipywidgets
import scipy.constants as const

from . import uvvis


class EnergyWavelengthTool:
    HC = const.Planck * const.c / const.electron_volt / const.nano

    def e2wl(self, e, digits=0):
        w = round(self.HC / e, digits)
        return w

    def wl2e(self, wl, digits=2):
        e = round(self.HC / wl, digits)
        return e

    def __init__(self):
        e0 = 3.5
        wl0 = self.e2wl(e0)
        emin = uvvis.EMIN
        emax = uvvis.EMAX
        wlmin = self.e2wl(emax)
        wlmax = self.e2wl(emin)
        style = {'description_width': '120px'}
        self._energy_slider = ipywidgets.FloatSlider(description="Energie / eV: ", min=emin, max=emax, step=0.01,
                                                     value=e0, readout_format='.2f', style=style)
        self._wavelength_slider = ipywidgets.FloatSlider(description="Wellenlänge / nm: ", min=wlmin, max=wlmax,
                                                         step=1.0, value=wl0,
                                                         readout_format='.0f', style=style)

        self._energy_slider.observe(self._on_change)
        self._wavelength_slider.observe(self._on_change)
        self._syncing = False

    def _on_change(self, change):
        if change["type"] == "change" and change["name"] == "value" and not self._syncing:
            self._syncing = True
            if change["owner"] == self._energy_slider:
                with self._wavelength_slider.hold_trait_notifications():
                    self._wavelength_slider.value = self.e2wl(self._energy_slider.value)
            elif change["owner"] == self._wavelength_slider:
                with self._energy_slider.hold_trait_notifications():
                    self._energy_slider.value = self.wl2e(self._wavelength_slider.value)
            self._syncing = False

    def show(self):
        IPython.display.display(self._energy_slider, self._wavelength_slider)
