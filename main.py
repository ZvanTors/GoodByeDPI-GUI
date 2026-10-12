"""Entry point for GoodByeDPI GUI."""
import logging
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.constants import APP_NAME, ORG_NAME
from app.core.controller import AppController
from app.core.logging_setup import setup_logging, get_log_file_path
from app.utils import is_admin

log = logging.getLogger(__name__)


def _install_excepthook() -> None:
    """Route uncaught exceptions to the log file and show a friendly dialog.

    Without this hook, an exception inside a Qt slot is silently printed to
    stderr — which does not exist in a windowed EXE. This turns silent
    crashes into actionable bug reports.
    """

    def _hook(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return

        log.critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_tb)
        )

        # Best-effort notification. The dialog itself must never crash.
        try:
            QMessageBox.critical(
                None,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n"
                f"{exc_type.__name__}: {exc_value}\n\n"
                f"A log file was saved to:\n{get_log_file_path()}",
            )
        except Exception:
            sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


def main() -> int:
    setup_logging()
    _install_excepthook()

    log.info("Starting %s", APP_NAME)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    # Tray mode keeps the app alive after the window is hidden.
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")  # Ensures QSS is rendered fully on Windows

    if not is_admin():
        QMessageBox.critical(
            None, "Administrator Required",
            "GoodByeDPI GUI must be run as Administrator.\n\n"
            "Right-click the app and choose 'Run as administrator'.",
        )
        return 1

    try:
        controller = AppController()
        controller.show()
        return app.exec()
    except Exception:
        log.exception("Fatal error during startup")
        raise


if __name__ == "__main__":
    sys.exit(main())