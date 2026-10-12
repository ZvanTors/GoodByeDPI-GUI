"""Persistent user settings (backed by QSettings)."""
from PySide6.QtCore import QSettings

from app.constants import ORG_NAME, APP_KEY, MODE_PRESETS


class AppSettings:
    def __init__(self) -> None:
        self._s = QSettings(ORG_NAME, APP_KEY)

    # --- Mode -----------------------------------------------------
    @property
    def mode_index(self) -> int:
        raw = int(self._s.value("mode_index", 0, type=int))
        # Clamp against the current preset list — guards against a stale
        # value if presets were ever re-ordered between releases.
        return max(0, min(raw, len(MODE_PRESETS) - 1))

    @mode_index.setter
    def mode_index(self, v: int) -> None:
        v = max(0, min(int(v), len(MODE_PRESETS) - 1))
        self._s.setValue("mode_index", v)

    # --- Custom args ---------------------------------------------
    @property
    def custom_args(self) -> str:
        return str(self._s.value("custom_args", "", type=str))

    @custom_args.setter
    def custom_args(self, v: str) -> None:
        self._s.setValue("custom_args", v)

    # --- Geometry ------------------------------------------------
    @property
    def geometry(self):
        return self._s.value("geometry")

    @geometry.setter
    def geometry(self, v) -> None:
        self._s.setValue("geometry", v)

    # --- Close behaviour -----------------------------------------
    @property
    def close_action(self) -> str:
        """One of: 'ask' | 'exit' | 'tray'."""
        raw = str(self._s.value("close_action", "ask", type=str))
        return raw if raw in ("ask", "exit", "tray") else "ask"

    @close_action.setter
    def close_action(self, v: str) -> None:
        if v not in ("ask", "exit", "tray"):
            v = "ask"
        self._s.setValue("close_action", v)

    def sync(self) -> None:
        self._s.sync()