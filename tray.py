"""System tray icon and its context menu."""
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from utils import resource_path


class TrayManager(QObject):
    """Encapsulates the system tray icon, menu, and status."""

    start_requested = Signal()
    stop_requested = Signal()
    exit_requested = Signal()
    restore_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self._icon = QSystemTrayIcon(parent)
        self._icon.setIcon(QIcon(resource_path("logo.ico")))
        self._icon.setToolTip("GoodByeDPI GUI - Stopped")

        self._menu = QMenu()

        self._start_action = QAction("▶  Start")
        self._start_action.triggered.connect(self.start_requested.emit)
        self._menu.addAction(self._start_action)

        self._stop_action = QAction("⏹  Stop")
        self._stop_action.setEnabled(False)
        self._stop_action.triggered.connect(self.stop_requested.emit)
        self._menu.addAction(self._stop_action)

        self._menu.addSeparator()

        self._status_action = QAction("Status: ● Stopped")
        self._status_action.setEnabled(False)
        self._menu.addAction(self._status_action)

        self._menu.addSeparator()

        self._exit_action = QAction("Exit")
        self._exit_action.triggered.connect(self.exit_requested.emit)
        self._menu.addAction(self._exit_action)

        self._icon.setContextMenu(self._menu)
        self._icon.activated.connect(self._on_activated)

    # --- Public API -----------------------------------------------
    def show(self) -> None:
        self._icon.show()

    def hide(self) -> None:
        self._icon.hide()

    def set_running(self, running: bool) -> None:
        if running:
            self._start_action.setEnabled(False)
            self._stop_action.setEnabled(True)
            self._status_action.setText("Status: ● Running")
            self._icon.setToolTip("GoodByeDPI GUI - Running")
        else:
            self._start_action.setEnabled(True)
            self._stop_action.setEnabled(False)
            self._status_action.setText("Status: ● Stopped")
            self._icon.setToolTip("GoodByeDPI GUI - Stopped")

    def show_message(self, title: str, message: str) -> None:
        self._icon.showMessage(title, message, QSystemTrayIcon.Information, 3000)

    # --- Internal --------------------------------------------------
    def _on_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.restore_requested.emit()