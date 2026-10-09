"""Application controller: wires UI, tray, settings, updater, and logic."""
import os
import subprocess

from PySide6.QtCore import QObject, QProcess, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from app.constants import (
    APP_VERSION,
    DPI_EXE_REL,
    MODE_PRESETS,
    TASK_NAME,
    download_url,
)
from app.ui.dialogs import (
    UpdateDialog,
    AboutDialog,
    CustomArgsHelpDialog,
)
from app.settings import AppSettings
from app.ui.tray import TrayManager
from app.ui.main_window import MainWindow
from app.core.updater import UpdateChecker
from app.utils import executable_path, resource_path
from app.validator import validate_args


DPI_EXE = resource_path(DPI_EXE_REL)
CUSTOM_MODE_INDEX = 2


class AppController(QObject):
    """Owns application state and orchestrates all components."""

    def __init__(self) -> None:
        super().__init__()

        self.settings = AppSettings()
        self.window = MainWindow()
        self.tray = TrayManager(self.window)
        self.updater = UpdateChecker(self)

        self.process: QProcess | None = None
        self.is_running = False
        self._saved_custom_args = self.settings.custom_args

        self._wire_signals()
        self._restore_state()

    # ------------------------------------------------------------------
    def _wire_signals(self) -> None:
        self.window.start_clicked.connect(self.start)
        self.window.stop_clicked.connect(self.stop)
        self.window.mode_changed.connect(self.on_mode_changed)
        self.window.custom_args_changed.connect(self.on_custom_args_changed)
        self.window.autostart_toggled.connect(self.on_autostart_toggled)
        self.window.close_choice.connect(self.on_close_choice)
        self.window.check_update_clicked.connect(self.check_for_updates_manual)
        self.window.clear_log_clicked.connect(self.window.clear_log)
        self.window.copy_log_clicked.connect(self.copy_log_to_clipboard)
        self.window.about_clicked.connect(self.show_about)
        self.window.custom_args_help_clicked.connect(self.show_custom_args_help)

        self.tray.start_requested.connect(self.start)
        self.tray.stop_requested.connect(self.stop)
        self.tray.exit_requested.connect(self.full_exit)
        self.tray.restore_requested.connect(self.restore_window)

        self.updater.update_available.connect(self.on_update_available)
        self.updater.up_to_date.connect(self.on_up_to_date)
        self.updater.error.connect(self.on_update_error)

    def _restore_state(self) -> None:
        geo = self.settings.geometry
        if geo is not None:
            self.window.restoreGeometry(geo)
            self._ensure_on_screen()

        idx = max(0, min(self.settings.mode_index, len(MODE_PRESETS) - 1))
        self.window.set_mode_index(idx)

        self.window.set_custom_args(self._saved_custom_args)
        self.window.set_autostart(self._is_autostart_enabled())

        self._apply_custom_args_state(idx)
        self._validate_custom_args()

    def _ensure_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        geo = self.window.geometry()
        if not avail.intersects(geo):
            self.window.resize(880, 700)
            self.window.move(
                avail.center().x() - 440,
                avail.center().y() - 350,
            )

    # ------------------------------------------------------------------
    def show(self) -> None:
        self.window.show()
        self.tray.show()
        self.tray.set_running(False)
        self.updater.check_async(manual=False)

    # ------------------------------------------------------------------
    @Slot()
    def start(self) -> None:
        if self.is_running:
            return

        self.settings.mode_index = self.window.mode_combo.currentIndex()
        self.settings.custom_args = self.window.custom_args_edit.text()
        self.settings.sync()

        idx = self.window.mode_combo.currentIndex()
        if idx == CUSTOM_MODE_INDEX:
            custom = self.window.custom_args_edit.text().strip()

            # --- Pre-start validation ---
            result = validate_args(custom)
            if result.has_errors:
                lines = "\n".join(f"   •  {e}" for e in result.errors)
                reply = QMessageBox.warning(
                    self.window,
                    "Invalid Arguments",
                    "The custom arguments contain errors:\n\n"
                    f"{lines}\n\n"
                    "Do you want to start anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return

            args = custom.split() if custom else []
        else:
            args = list(MODE_PRESETS[idx][1])

        if not os.path.exists(DPI_EXE):
            QMessageBox.critical(
                self.window, "Error",
                f"GoodbyeDPI executable not found:\n{DPI_EXE}",
            )
            return

        self.process = QProcess(self)
        self.process.setProgram(DPI_EXE)
        self.process.setArguments(args)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._handle_output)
        self.process.finished.connect(self._on_process_finished)
        self.process.errorOccurred.connect(self._on_process_error)

        self.is_running = True
        self.process.start()

        if not self.process.waitForStarted(3000):
            self.is_running = False
            self.process.deleteLater()
            self.process = None
            QMessageBox.critical(
                self.window, "Error",
                "Failed to start GoodbyeDPI.\n"
                "Make sure the app is running as Administrator.",
            )
            return

        self.window.set_running_state(True)
        self.tray.set_running(True)
        self.window.append_log("─── GoodbyeDPI started ───")

    @Slot()
    def stop(self) -> None:
        if self.process and self.is_running:
            self.process.kill()
            self.process.waitForFinished(2000)

    @Slot()
    def _handle_output(self) -> None:
        if self.process is None:
            return
        data = self.process.readAllStandardOutput()
        if data:
            text = bytes(data).decode("utf-8", errors="replace").rstrip()
            self.window.append_log(text)

    def _on_process_finished(self, *_):
        if not self.is_running:
            return
        self.is_running = False
        self.window.set_running_state(False)
        self.tray.set_running(False)
        self.window.append_log("─── GoodbyeDPI stopped ───")

        if self.process is not None:
            self.process.deleteLater()
            self.process = None

    def _on_process_error(self, error) -> None:
        if error == QProcess.FailedToStart:
            self.is_running = False
            self.window.append_log("[error] Process failed to start.")

    # ------------------------------------------------------------------
    # Mode / custom args
    # ------------------------------------------------------------------
    def _apply_custom_args_state(self, mode_idx: int) -> None:
        is_custom = (mode_idx == CUSTOM_MODE_INDEX)
        self.window.set_custom_args_visible(is_custom)

    @Slot(int)
    def on_mode_changed(self, idx: int) -> None:
        if idx == CUSTOM_MODE_INDEX:
            self.window.set_custom_args(self._saved_custom_args)
        else:
            self._saved_custom_args = self.window.custom_args_edit.text()

        self._apply_custom_args_state(idx)
        self._validate_custom_args()

    @Slot(str)
    def on_custom_args_changed(self, text: str) -> None:
        self._saved_custom_args = text
        self._validate_custom_args()

    def _validate_custom_args(self) -> None:
        result = validate_args(self.window.custom_args_edit.text())
        self.window.set_args_validation(result.errors, result.warnings)

    # ------------------------------------------------------------------
    # Custom arguments help
    # ------------------------------------------------------------------
    @Slot()
    def show_custom_args_help(self) -> None:
        dlg = CustomArgsHelpDialog(
            self.window,
            self.window.custom_args_edit.text(),
        )
        if dlg.exec() == QDialog.Accepted:
            new_args = dlg.result_args()
            self.window.custom_args_edit.setText(new_args)
            self._saved_custom_args = new_args
            self._validate_custom_args()

    # ------------------------------------------------------------------
    # Autostart
    # ------------------------------------------------------------------
    def _is_autostart_enabled(self) -> bool:
        try:
            r = subprocess.run(
                ["schtasks", "/query", "/tn", TASK_NAME],
                capture_output=True, text=True, timeout=5,
            )
            return TASK_NAME in (r.stdout or "")
        except Exception:
            return False

    @Slot(bool)
    def on_autostart_toggled(self, checked: bool) -> None:
        try:
            if checked:
                exe = executable_path()
                subprocess.run(
                    ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
                    capture_output=True,
                )
                subprocess.run(
                    ["schtasks", "/create", "/tn", TASK_NAME,
                     "/tr", f'"{exe}"', "/sc", "onlogon",
                     "/rl", "highest", "/f"],
                    capture_output=True, check=True, text=True,
                )
                QMessageBox.information(
                    self.window, "Success", "Startup task created.",
                )
            else:
                subprocess.run(
                    ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
                    capture_output=True, check=True, text=True,
                )
                QMessageBox.information(
                    self.window, "Success", "Startup task removed.",
                )
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self.window, "Error",
                f"Failed to update task:\n{e.stderr or e.stdout or e}",
            )
        finally:
            self.window.set_autostart(self._is_autostart_enabled())

    # ------------------------------------------------------------------
    # Window / Tray
    # ------------------------------------------------------------------
    @Slot(str)
    def on_close_choice(self, choice: str) -> None:
        if choice == "exit":
            self.full_exit()
        elif choice == "tray":
            self.window.hide()
            self.tray.show()

    @Slot()
    def restore_window(self) -> None:
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()

    @Slot()
    def full_exit(self) -> None:
        if self.is_running:
            self.stop()
        self.settings.geometry = self.window.saveGeometry()
        self.settings.sync()
        self.tray.hide()
        QApplication.quit()

    # ------------------------------------------------------------------
    @Slot()
    def copy_log_to_clipboard(self) -> None:
        text = self.window.copy_log()
        if not text.strip():
            self.window.show_info("Copy Log", "The log is empty.")
            return
        QApplication.clipboard().setText(text)
        self.window.show_info("Copy Log", "Log copied to clipboard.")

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------
    @Slot()
    def show_about(self) -> None:
        dlg = AboutDialog(self.window, APP_VERSION)
        dlg.exec()

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    @Slot()
    def check_for_updates_manual(self) -> None:
        self.updater.check_async(manual=True)

    @Slot(str)
    def on_update_available(self, new_version: str) -> None:
        dlg = UpdateDialog(self.window, APP_VERSION, new_version)
        if dlg.exec() == QDialog.Accepted:
            self._open_download(new_version)

    @Slot()
    def on_up_to_date(self) -> None:
        self.window.show_info(
            "Check for updates",
            f"You are running the latest version (v{APP_VERSION}).",
        )

    @Slot()
    def on_update_error(self) -> None:
        self.window.show_info(
            "Check for updates",
            "Couldn't check for updates.\n"
            "Please verify your internet connection and try again.",
        )

    def _open_download(self, version: str) -> None:
        url = download_url(version)
        QDesktopServices.openUrl(QUrl(url))