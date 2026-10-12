"""Application controller: wires UI, tray, settings, updater, and logic."""
import logging
import os
import subprocess

from PySide6.QtCore import QObject, QProcess, QTimer, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox, QDialog

from app.constants import (
    APP_VERSION,
    DPI_EXE_REL,
    MODE_PRESETS,
    CUSTOM_MODE_INDEX,
    TASK_NAME,
    DONATION_WALLETS,
    download_url,
)
from app.ui.dialogs import (
    UpdateDialog,
    AboutDialog,
    CustomArgsHelpDialog,
    DonateDialog,
)
from app.settings import AppSettings
from app.ui.tray import TrayManager
from app.ui.main_window import MainWindow
from app.core.updater import UpdateChecker
from app.utils import executable_path, resource_path
from app.validator import validate_args

log = logging.getLogger(__name__)

DPI_EXE = resource_path(DPI_EXE_REL)

# How long to wait for graceful termination before killing.
_STOP_GRACE_MS = 1500
# Timeout for schtasks calls (must stay below UI-perceptible thresholds).
_SCHTASKS_TIMEOUT_S = 10


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
        self._stopping = False
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
        self.window.donate_clicked.connect(self.show_donate)
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

        self._apply_custom_args_state(idx, animate=False)
        self._validate_custom_args()

    def _ensure_on_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        avail = screen.availableGeometry()
        geo = self.window.geometry()
        # Require a meaningful overlap — a 1px intersection is not
        # "on screen", it's a broken layout.
        min_visible_px = 100
        inter = avail.intersected(geo)
        if inter.width() < min_visible_px or inter.height() < min_visible_px:
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

        idx = self.window.current_mode_index()
        self.settings.mode_index = idx

        if idx == CUSTOM_MODE_INDEX:
            custom = self.window.custom_args_edit.text().strip()
            self.settings.custom_args = custom
            self._saved_custom_args = custom
        else:
            # Never overwrite the saved custom args just because the user
            # happened to be on Fast/Compatible mode.
            self.settings.custom_args = self._saved_custom_args

        self.settings.sync()

        if idx == CUSTOM_MODE_INDEX:
            custom = self.window.custom_args_edit.text().strip()

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
            args = list(MODE_PRESETS[idx].args)

        if not os.path.exists(DPI_EXE):
            log.error("GoodbyeDPI executable missing at %s", DPI_EXE)
            QMessageBox.critical(
                self.window, "Error",
                f"GoodbyeDPI executable not found:\n{DPI_EXE}",
            )
            return

        try:
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
                raise RuntimeError("waitForStarted timed out")
        except Exception as exc:
            log.exception("Failed to start GoodbyeDPI: %s", exc)
            self.is_running = False
            if self.process is not None:
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
        """Request a graceful stop; force-kill after a short grace period.

        Runs entirely on the Qt event loop — no blocking waitForFinished
        on the UI thread.
        """
        if not self.is_running or self.process is None:
            return
        if self._stopping:
            return

        self._stopping = True
        log.info("Stopping GoodbyeDPI (graceful)")
        self.process.terminate()
        QTimer.singleShot(_STOP_GRACE_MS, self._force_kill_if_needed)

    def _force_kill_if_needed(self) -> None:
        if (self._stopping
                and self.process is not None
                and self.process.state() != QProcess.NotRunning):
            log.warning("Process did not exit in time; killing")
            self.process.kill()

    @Slot()
    def _handle_output(self) -> None:
        proc = self.process
        if proc is None:
            return
        try:
            data = proc.readAllStandardOutput()
            if data:
                text = bytes(data).decode("utf-8", errors="replace").rstrip()
                self.window.append_log(text)
        except RuntimeError as exc:
            # Can happen if the C++ object was already deleted.
            log.debug("readAll after process deleted: %s", exc)

    def _on_process_finished(self, *_):
        if not self.is_running:
            return
        self.is_running = False
        self._stopping = False
        self.window.set_running_state(False)
        self.tray.set_running(False)
        self.window.append_log("─── GoodbyeDPI stopped ───")

        if self.process is not None:
            self.process.deleteLater()
            self.process = None

    def _on_process_error(self, error) -> None:
        if error == QProcess.FailedToStart:
            self.is_running = False
            self._stopping = False
            self.window.append_log("[error] Process failed to start.")
            log.error("QProcess failed to start")

    # ------------------------------------------------------------------
    # Mode / custom args
    # ------------------------------------------------------------------
    def _apply_custom_args_state(
        self, mode_idx: int, animate: bool = True
    ) -> None:
        is_custom = (mode_idx == CUSTOM_MODE_INDEX)
        self.window.set_custom_args_visible(is_custom, animate=animate)

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
        """Return True only when our exact task exists.

        The old implementation did a substring search on stdout, which
        matched any task whose name *contained* TASK_NAME (e.g. a
        leftover ``GoodbyeDPIManager_old``).
        """
        try:
            r = subprocess.run(
                ["schtasks", "/query", "/tn", TASK_NAME,
                 "/fo", "CSV", "/nh"],
                capture_output=True, text=True,
                timeout=_SCHTASKS_TIMEOUT_S, shell=False,
            )
            if r.returncode != 0:
                return False
            first_line = (r.stdout or "").strip().splitlines()[0] \
                if r.stdout else ""
            # CSV: "TaskName","Next Run Time","Status"
            # A substring match on TASK_NAME would still produce false
            # positives here, so we match the first field exactly.
            return (
                first_line.startswith(f'"{TASK_NAME}"')
                or first_line.startswith(f"{TASK_NAME},")
            )
        except Exception as exc:
            log.debug("autostart query failed: %s", exc)
            return False

    @Slot(bool)
    def on_autostart_toggled(self, checked: bool) -> None:
        try:
            if checked:
                exe = executable_path()
                subprocess.run(
                    ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
                    capture_output=True, shell=False,
                    timeout=_SCHTASKS_TIMEOUT_S,
                )
                subprocess.run(
                    ["schtasks", "/create", "/tn", TASK_NAME,
                     "/tr", f'"{exe}"', "/sc", "onlogon",
                     "/rl", "highest", "/f"],
                    capture_output=True, check=True, text=True,
                    timeout=_SCHTASKS_TIMEOUT_S, shell=False,
                )
                self.window.show_toast("Startup task created", "success")
            else:
                subprocess.run(
                    ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
                    capture_output=True, check=True, text=True,
                    timeout=_SCHTASKS_TIMEOUT_S, shell=False,
                )
                self.window.show_toast("Startup task removed", "success")
        except subprocess.TimeoutExpired:
            log.error("schtasks timed out")
            QMessageBox.critical(
                self.window, "Error",
                "The system command timed out. Please try again.",
            )
        except subprocess.CalledProcessError as exc:
            log.error("schtasks failed: %s", exc)
            QMessageBox.critical(
                self.window, "Error",
                f"Failed to update task:\n{exc.stderr or exc.stdout or exc}",
            )
        except Exception as exc:
            log.exception("Unexpected error updating autostart")
            QMessageBox.critical(
                self.window, "Error",
                f"Unexpected error:\n{exc}",
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
        # Give the child process a clean, bounded shutdown so it doesn't
        # outlive the GUI as an orphan.
        if self.process is not None and self.is_running:
            try:
                self.process.kill()
                self.process.waitForFinished(2000)
            except Exception as exc:
                log.warning("Error while killing process on exit: %s", exc)

        try:
            self.settings.geometry = self.window.saveGeometry()
            self.settings.sync()
        except Exception as exc:
            log.warning("Could not persist geometry on exit: %s", exc)

        self.tray.hide()
        QApplication.quit()

    # ------------------------------------------------------------------
    @Slot()
    def copy_log_to_clipboard(self) -> None:
        text = self.window.copy_log()
        if not text.strip():
            self.window.show_toast("The log is empty", "warning")
            return
        try:
            QApplication.clipboard().setText(text)
            self.window.show_toast("Log copied to clipboard", "success")
        except Exception as exc:
            log.exception("copy_log failed: %s", exc)
            self.window.show_toast("Could not copy log", "error")

    # ------------------------------------------------------------------
    # About
    # ------------------------------------------------------------------
    @Slot()
    def show_about(self) -> None:
        try:
            AboutDialog(self.window, APP_VERSION).exec()
        except Exception as exc:
            log.exception("AboutDialog failed: %s", exc)

    # ------------------------------------------------------------------
    # Donate
    # ------------------------------------------------------------------
    @Slot()
    def show_donate(self) -> None:
        try:
            DonateDialog(self.window, DONATION_WALLETS).exec()
        except Exception as exc:
            log.exception("DonateDialog failed: %s", exc)

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------
    @Slot()
    def check_for_updates_manual(self) -> None:
        self.updater.check_async(manual=True)

    @Slot(str)
    def on_update_available(self, new_version: str) -> None:
        try:
            dlg = UpdateDialog(self.window, APP_VERSION, new_version)
            if dlg.exec() == QDialog.Accepted:
                self._open_download(new_version)
        except Exception as exc:
            log.exception("UpdateDialog failed: %s", exc)

    @Slot()
    def on_up_to_date(self) -> None:
        self.window.show_toast(
            f"You're on the latest version (v{APP_VERSION})",
            "success",
            4000,
        )

    @Slot()
    def on_update_error(self) -> None:
        self.window.show_toast(
            "Couldn't check for updates — verify your connection",
            "warning",
            4500,
        )

    def _open_download(self, version: str) -> None:
        try:
            url = download_url(version)
        except ValueError as exc:
            log.error("Bad version for download: %s", exc)
            self.window.show_toast("Invalid download URL", "error")
            return
        ok = QDesktopServices.openUrl(QUrl(url))
        if not ok:
            log.warning("openUrl returned False for %s", url)
            self.window.show_toast(
                "Could not open browser — copy the URL manually", "warning",
            )