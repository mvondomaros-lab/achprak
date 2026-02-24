import asyncio

import IPython.display
import ipywidgets as widgets
import nglview


class NGLAccordion:
    """
    Lazy nglview inside an Accordion.

    The NGL widget is created only when the accordion is opened to avoid
    WebGL initialization at 0×0 size.
    """

    def __init__(
        self, title: str = "3D-Struktur", width: str = "100%", height: str = "600px"
    ):
        self.title = title
        self.width = width
        self.height = height

        self._slot = widgets.Output(layout=widgets.Layout(width="100%"))
        self.accordion = widgets.Accordion([self._slot], titles=[self.title])
        self.accordion.observe(self._on_open, names="selected_index")

        self.ngl_view: nglview.NGLWidget | None = None
        self._pending: tuple[str, object] | None = None

    def show(self, output: widgets.Output) -> None:
        with output:
            IPython.display.display(self.accordion)

    def clear(self) -> None:
        if self.ngl_view is None:
            self._pending = None
            return

        for component in list(self.ngl_view):
            self.ngl_view.remove_component(component)

        self._resize()

    def show_atoms(self, atoms) -> None:
        if self.ngl_view is None:
            self._pending = ("atoms", atoms)
            return

        self.clear()
        self.ngl_view.add_component(nglview.ASEStructure(atoms))
        self.ngl_view.center()
        self._resize()

    def show_traj(self, traj) -> None:
        if self.ngl_view is None:
            self._pending = ("traj", traj)
            return

        self.clear()
        self.ngl_view.add_trajectory(nglview.ASETrajectory(traj))
        self.ngl_view.center()
        self._resize()

    def close(self) -> None:
        if self.ngl_view is not None:
            try:
                self.ngl_view.close()
            finally:
                self.ngl_view = None

        with self._slot:
            self._slot.clear_output(wait=True)

    def _on_open(self, change) -> None:
        if change.get("new") == 0:
            self._ensure_view()

    def _ensure_view(self) -> None:
        if self.ngl_view is not None:
            self._resize(delay=150)
            return

        with self._slot:
            self._slot.clear_output(wait=True)

            self.ngl_view = nglview.NGLWidget()
            self.ngl_view.layout = widgets.Layout(width=self.width, height=self.height)
            IPython.display.display(self.ngl_view)

        self._resize(delay=250)

        if self._pending is not None:
            kind, payload = self._pending
            self._pending = None

            if kind == "atoms":
                self.show_atoms(payload)
            elif kind == "traj":
                self.show_traj(payload)

    def _resize(self, delay: int = 100) -> None:
        if self.ngl_view is None:
            return

        self.ngl_view._js(
            f"""
        setTimeout(() => {{
          try {{ this.handleResize(); }} catch (e) {{}}
          try {{ this.stage?.viewer?.requestRender(); }} catch (e) {{}}
        }}, {int(delay)});
        """
        )


def flash_button(button, message: str, seconds: float = 0.5) -> None:
    """
    Temporarily change button label and disable it.
    Prevents overlapping flashes.
    """
    # Guard: ignore if already flashing
    if getattr(button, "_flashing", False):
        return

    button._flashing = True

    original_desc = button.description
    original_disabled = button.disabled

    button.disabled = True
    button.description = message

    async def restore_later() -> None:
        try:
            await asyncio.sleep(seconds)
            button.description = original_desc
            button.disabled = original_disabled
        finally:
            button._flashing = False

    asyncio.create_task(restore_later())
