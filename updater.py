"""Check GitHub for the latest release."""
import re
import urllib.request

from PySide6.QtCore import QObject, Signal, QThread

from constants import RELEASES_LATEST, APP_VERSION
from utils import is_newer_version


class _UpdateWorker(QThread):
    """Background worker that scrapes the /releases/latest redirect."""
    found = Signal(str)       # emits new version string, e.g. "1.2.0"
    not_found = Signal()      # emitted when no newer version or network error

    def run(self) -> None:
        try:
            req = urllib.request.Request(
                RELEASES_LATEST,
                headers={"User-Agent": "Mozilla/5.0 GoodByeDPI-GUI-Updater"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                final_url = response.url

            # final_url looks like: .../releases/tag/V1.2.0
            m = re.search(r"/tag/[vV]?([0-9]+(?:\.[0-9]+)*)", final_url)
            if not m:
                self.not_found.emit()
                return
            latest = m.group(1)
            if is_newer_version(APP_VERSION, latest):
                self.found.emit(latest)
            else:
                self.not_found.emit()
        except Exception:
            self.not_found.emit()


class UpdateChecker(QObject):
    """High-level API for checking updates."""

    update_available = Signal(str)  # new version string
    up_to_date = Signal()           # emitted only for manual checks

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._worker: _UpdateWorker | None = None

    def check_async(self, manual: bool = False) -> None:
        """Start a background check. If `manual`, emit `up_to_date` when nothing found."""
        if self._worker is not None and self._worker.isRunning():
            return
        worker = _UpdateWorker(self)
        worker.found.connect(self.update_available)
        if manual:
            worker.not_found.connect(self.up_to_date)
        self._worker = worker
        worker.start()