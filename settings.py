"""Persistent user settings (backed by QSettings)."""
from PySide6.QtCore import QSettings

from constants import ORG_NAME, APP_KEY


class AppSettings:
    def __init__(self) -> None:
        self._s = QSettings(ORG_NAME, APP_KEY)

    # --- Mode -----------------------------------------------------
    @property
    def mode_index(self) -> int:
        return int(self._s.value("mode_index", 0, type=int))

    @mode_index.setter
    def mode_index(self, v: int) -> None:
        self._s.setValue("mode_index", int(v))

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

    def sync(self) -> None:
        self._s.sync()