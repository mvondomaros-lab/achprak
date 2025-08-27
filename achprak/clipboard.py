class Clipboard:
    def __init__(self):
        self._content = ""  # internal storage for clipboard content

    def copy(self, text: str) -> None:
        """Copy text into the clipboard."""
        self._content = text

    def paste(self) -> str:
        """Return the current clipboard content."""
        return self._content


# Instantiate a single global clipboard object
clipboard = Clipboard()
