"""Check GitHub for the latest release."""
import logging
import re
import time
import urllib.request

from PySide6.QtCore import QObject, Signal, QThread

from app.constants import RELEASES_LATEST, APP_VERSION
from app.utils import is_newer_version

log = logging.getLogger(__name__)


class _UpdateWorker(QThread):
    """Background worker that scrapes the /releases/latest redirect."""

    found = Signal(str)
    not_found = Signal()
    error = Signal()

    def run(self) -> None:
        try:
            req = urllib.request.Request(
                RELEASES_LATEST,
                headers={"User-Agent": "Mozilla/5.0 GoodByeDPI-GUI-Updater"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                final_url = response.url

            m = re.search(r"/tag/[vV]?([0-9]+(?:\.[0-9]+)*)", final_url)
            if not m:
                log.warning("Updater: could not parse version from %s", final_url)
                self.error.emit()
                return

            latest = m.group(1)
            if is_newer_version(APP_VERSION, latest):
                self.found.emit(latest)
            else:
                self.not_found.emit()
        except Exception as exc:
            log.info("Update check failed: %s", exc)
            self.error.emit()


class UpdateChecker(QObject):
    """High-level API for checking updates."""

    update_available = Signal(str)
    up_to_date = Signal()
    error = Signal()
    #: Emitted after *any* check finishes (manual or silent). Controllers
    #: use this to reset busy indicators.
    finished = Signal()

    #: Minimum interval between silent (non-manual) checks, in seconds.
    _SILENT_INTERVAL_S = 60.0

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._worker: _UpdateWorker | None = None
        self._last_check_ts: float = 0.0

    def check_async(self, manual: bool = False) -> bool:
        """Start a background check.

        Returns True if a worker was actually started, False if a check
        is already running or the call was rate-limited.
        """
        if self._worker is not None and self._worker.isRunning():
            return False

        now = time.monotonic()
        if (not manual
                and (now - self._last_check_ts) < self._SILENT_INTERVAL_S):
            log.debug("Silent update check skipped (rate-limited)")
            return False
        self._last_check_ts = now

        worker = _UpdateWorker(self)
        worker.found.connect(self.update_available)
        if manual:
            worker.not_found.connect(self.up_to_date)
            worker.error.connect(self.error)

        # Prevent QThread leak: delete when the thread finishes.
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(self._on_worker_finished)

        self._worker = worker
        worker.start()
        return True

    def _on_worker_finished(self) -> None:
        self._worker = None
        self.finished.emit()