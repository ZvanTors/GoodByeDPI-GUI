import sys
import os
import re
import subprocess
import ctypes
import urllib.request
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QLineEdit,
    QCheckBox, QMessageBox, QGroupBox, QMenu, QSystemTrayIcon,
    QFrame
)
from PySide6.QtCore import Qt, QProcess, Signal, Slot, QSettings, QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QAction


# ---------------- Helpers ----------------
def resource_path(relative_path: str) -> str:
    """Get absolute path to resource (works for dev and PyInstaller)."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


DPI_EXE = resource_path("goodbyedpi.exe")

# 🔹 Current version of the GUI
CURRENT_VERSION = "1.1.0"
RELEASES_LATEST_URL = "https://github.com/ZvanTors/GoodByeDPI-GUI/releases/latest"
RELEASES_URL = "https://github.com/ZvanTors/GoodByeDPI-GUI/releases"
TASK_NAME = "GoodbyeDPIManager"


# ---------------- Modern Dark Theme ----------------
DARK_QSS = """
QMainWindow, QWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Inter', 'Tahoma', sans-serif;
    font-size: 10pt;
}
QGroupBox {
    background-color: #252537;
    border: 1px solid #313244;
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 10px 10px 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: #89b4fa;
}
QLabel { color: #cdd6f4; background: transparent; }

QLabel#appTitle {
    font-size: 16pt;
    font-weight: 700;
    color: #f5f5f5;
}
QLabel#versionBadge {
    background-color: #313244;
    color: #a6e3a1;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 9pt;
    font-weight: 600;
}
QLabel#creditLabel {
    color: #7f849c;
    font-size: 8pt;
}
QLabel#statusLabel {
    font-weight: 600;
    padding: 0 6px;
}

QComboBox, QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 6px 10px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
}
QComboBox:hover, QLineEdit:hover { border: 1px solid #585b70; }
QComboBox:focus, QLineEdit:focus { border: 1px solid #89b4fa; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #313244;
    border: 1px solid #45475a;
    selection-background-color: #89b4fa;
    color: #cdd6f4;
}
QLineEdit:disabled {
    background-color: #1e1e2e;
    color: #6c7086;
    border: 1px solid #313244;
}

QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 8px 18px;
    color: #cdd6f4;
    font-weight: 600;
    min-width: 90px;
}
QPushButton:hover { background-color: #45475a; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled { color: #6c7086; background-color: #252537; }

QPushButton#startBtn { background-color: #a6e3a1; color: #1e1e2e; border: none; }
QPushButton#startBtn:hover { background-color: #94e2d5; }
QPushButton#startBtn:disabled { background-color: #313244; color: #6c7086; }

QPushButton#stopBtn { background-color: #f38ba8; color: #1e1e2e; border: none; }
QPushButton#stopBtn:hover { background-color: #eba0ac; }
QPushButton#stopBtn:disabled { background-color: #313244; color: #6c7086; }

QTextEdit {
    background-color: #181825;
    border: 1px solid #313244;
    border-radius: 6px;
    padding: 8px;
    color: #a6e3a1;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
}

QCheckBox { spacing: 8px; color: #cdd6f4; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border-radius: 4px;
    border: 1px solid #585b70;
    background-color: #313244;
}
QCheckBox::indicator:hover { border: 1px solid #89b4fa; }
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border: 1px solid #89b4fa;
}

QMenu {
    background-color: #252537;
    border: 1px solid #313244;
    border-radius: 8px;
    padding: 6px;
    color: #cdd6f4;
}
QMenu::item { padding: 6px 22px; border-radius: 4px; }
QMenu::item:selected { background-color: #89b4fa; color: #1e1e2e; }
QMenu::separator { height: 1px; background: #313244; margin: 4px 8px; }

QScrollBar:vertical {
    background: #181825; width: 10px; border-radius: 5px; margin: 0;
}
QScrollBar::handle:vertical {
    background: #45475a; border-radius: 5px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QFrame#headerFrame {
    background-color: #252537;
    border-radius: 10px;
    border: 1px solid #313244;
}
"""


class GoodbyeDPIManager(QMainWindow):
    log_signal = Signal(str)
    update_found_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoodByeDPI GUI")
        self.setWindowIcon(QIcon(resource_path("logo.ico")))
        self.setStyleSheet(DARK_QSS)

        # --- State ---
        self.process: QProcess | None = None
        self.is_running = False

        # --- Settings ---
        self.settings = QSettings("GoodbyeDPIManager", "GUI")
        self.mode_index = self.settings.value("mode_index", 0, type=int)
        self.custom_args = self.settings.value("custom_args", "", type=str)
        # Keep user's custom args in a safe place
        self._saved_custom_args = self.custom_args

        # Restore window geometry
        geo = self.settings.value("geometry")
        if geo is not None:
            self.restoreGeometry(geo)
        else:
            self.resize(720, 560)
        self.setMinimumSize(600, 500)

        # --- System Tray ---
        self._build_tray()

        # --- Central UI ---
        self._build_ui()

        # --- Signals ---
        self.log_signal.connect(self.append_log)
        self.update_found_signal.connect(self.show_update_notification)

        # --- Initial UI state ---
        self.update_autostart_check()
        self.on_mode_changed()
        self.update_tray_status()

        # --- Background update check ---
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("logo.ico")))
        self.tray_icon.setToolTip("GoodByeDPI GUI - Stopped")

        self.tray_menu = QMenu()

        self.tray_start_action = QAction("▶  Start", self)
        self.tray_start_action.triggered.connect(self.start_goodbyedpi)
        self.tray_menu.addAction(self.tray_start_action)

        self.tray_stop_action = QAction("⏹  Stop", self)
        self.tray_stop_action.triggered.connect(self.stop_goodbyedpi)
        self.tray_stop_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_stop_action)

        self.tray_menu.addSeparator()

        self.tray_status_action = QAction("Status: ● Stopped", self)
        self.tray_status_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_status_action)

        self.tray_menu.addSeparator()

        self.tray_exit_action = QAction("Exit", self)
        self.tray_exit_action.triggered.connect(self.full_exit)
        self.tray_menu.addAction(self.tray_exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 12)
        root.setSpacing(12)

        # ---------- Header ----------
        header = QFrame()
        header.setObjectName("headerFrame")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)

        title = QLabel("🛡  GoodByeDPI GUI")
        title.setObjectName("appTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()

        version_badge = QLabel(f"v{CURRENT_VERSION}")
        version_badge.setObjectName("versionBadge")
        header_layout.addWidget(version_badge)

        root.addWidget(header)

        # ---------- Settings group ----------
        settings_group = QGroupBox("DPI Circumvention Settings")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "-6  (Recommended)",
            "-5  (General)",
            "Custom"
        ])
        self.mode_combo.setCurrentIndex(min(max(self.mode_index, 0), 2))
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        mode_layout.addWidget(self.mode_combo, 1)
        settings_layout.addLayout(mode_layout)

        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom arguments:"))
        self.custom_args_edit = QLineEdit(self._saved_custom_args)
        self.custom_args_edit.setPlaceholderText(
            "e.g.  -f 2 -e 40 --native-frag --reverse-frag"
        )
        custom_layout.addWidget(self.custom_args_edit, 1)
        settings_layout.addLayout(custom_layout)

        self.autostart_check = QCheckBox("Run on Windows startup (Task Scheduler)")
        self.autostart_check.toggled.connect(self.toggle_autostart)
        settings_layout.addWidget(self.autostart_check)

        root.addWidget(settings_group)

        # ---------- Controls ----------
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_goodbyedpi)

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_goodbyedpi)

        self.status_label = QLabel("● Stopped")
        self.status_label.setObjectName("statusLabel")
        self._set_status_style(running=False)

        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addSpacing(12)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()

        root.addLayout(control_layout)

        # ---------- Output log ----------
        log_group = QGroupBox("Output")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(10, 14, 10, 10)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        log_layout.addWidget(self.log_view)
        root.addWidget(log_group, 1)

        # ---------- Bottom bar ----------
        bottom = QHBoxLayout()
        self.footer_version = QLabel(f"Version {CURRENT_VERSION}")
        self.footer_version.setStyleSheet("color: #7f849c; font-size: 9pt;")
        bottom.addWidget(self.footer_version)
        bottom.addStretch()
        credit = QLabel("Made with ❤️  by AmooReza (WhiteDNS)")
        credit.setObjectName("creditLabel")
        bottom.addWidget(credit)
        root.addLayout(bottom)

    def _set_status_style(self, running: bool):
        if running:
            self.status_label.setText("● Running")
            self.status_label.setStyleSheet("color: #a6e3a1; font-weight: 600;")
        else:
            self.status_label.setText("● Stopped")
            self.status_label.setStyleSheet("color: #f38ba8; font-weight: 600;")

    # ------------------------------------------------------------------
    # Autostart
    # ------------------------------------------------------------------
    def is_autostart_enabled(self) -> bool:
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/tn", TASK_NAME],
                capture_output=True, text=True, timeout=5
            )
            return TASK_NAME in (result.stdout or "")
        except Exception:
            return False

    def update_autostart_check(self):
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(self.is_autostart_enabled())
        self.autostart_check.blockSignals(False)

    def toggle_autostart(self, checked: bool):
        try:
            if checked:
                exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
                subprocess.run(
                    ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
                    capture_output=True
                )
                subprocess.run(
                    ["schtasks", "/create", "/tn", TASK_NAME,
                     "/tr", f'"{exe_path}"', "/sc", "onlogon",
                     "/rl", "highest", "/f"],
                    capture_output=True, check=True, text=True
                )
                QMessageBox.information(self, "Success", "Startup task created.")
            else:
                subprocess.run(
                    ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
                    capture_output=True, check=True, text=True
                )
                QMessageBox.information(self, "Success", "Startup task removed.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(
                self, "Error",
                f"Failed to update task:\n{e.stderr or e.stdout or e}"
            )
        finally:
            self.update_autostart_check()

    # ------------------------------------------------------------------
    # Mode
    # ------------------------------------------------------------------
    def on_mode_changed(self):
        idx = self.mode_combo.currentIndex()
        custom = (idx == 2)
        self.custom_args_edit.setEnabled(custom)
        # Remember the user's value so switching back restores it
        if custom:
            self.custom_args_edit.setText(self._saved_custom_args)
        else:
            self._saved_custom_args = self.custom_args_edit.text()

    # ------------------------------------------------------------------
    # Start / Stop
    # ------------------------------------------------------------------
    def start_goodbyedpi(self):
        if self.is_running:
            return

        # Persist settings
        self.settings.setValue("mode_index", self.mode_combo.currentIndex())
        self.settings.setValue("custom_args", self.custom_args_edit.text())
        self.settings.setValue("geometry", self.saveGeometry())

        idx = self.mode_combo.currentIndex()
        if idx == 0:
            args = ["-6"]
        elif idx == 1:
            args = ["-5"]
        else:
            custom = self.custom_args_edit.text().strip()
            args = custom.split() if custom else []

        if not os.path.exists(DPI_EXE):
            QMessageBox.critical(
                self, "Error",
                f"GoodbyeDPI executable not found:\n{DPI_EXE}"
            )
            return

        self.process = QProcess(self)
        self.process.setProgram(DPI_EXE)
        self.process.setArguments(args)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.on_process_finished)
        self.process.errorOccurred.connect(self.on_process_error)

        # Mark running BEFORE start to avoid a race in on_process_finished
        self.is_running = True
        self.process.start()

        if not self.process.waitForStarted(3000):
            self.is_running = False
            QMessageBox.critical(
                self, "Error",
                "Failed to start GoodbyeDPI.\nMake sure you are running as Administrator."
            )
            self.process = None
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._set_status_style(True)
        self.log_signal.emit("─── GoodbyeDPI started ───")
        self.update_tray_status()

    def stop_goodbyedpi(self):
        if self.process and self.is_running:
            self.process.kill()
            self.process.waitForFinished(2000)

    def handle_output(self):
        if self.process is None:
            return
        data = self.process.readAllStandardOutput()
        if data:
            text = bytes(data).decode('utf-8', errors='replace')
            self.log_signal.emit(text.rstrip())

    @Slot(int, QProcess.ExitStatus)
    def on_process_finished(self, *_):
        # Guard against being called twice (signal + manual)
        if not self.is_running:
            return
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self._set_status_style(False)
        self.log_signal.emit("─── GoodbyeDPI stopped ───")
        self.update_tray_status()

    def on_process_error(self, error):
        if error == QProcess.FailedToStart:
            self.is_running = False
            self.log_signal.emit("[error] Process failed to start.")

    # ------------------------------------------------------------------
    # Tray
    # ------------------------------------------------------------------
    def update_tray_status(self):
        if self.is_running:
            self.tray_start_action.setEnabled(False)
            self.tray_stop_action.setEnabled(True)
            self.tray_status_action.setText("Status: ● Running")
            self.tray_icon.setToolTip("GoodByeDPI GUI - Running")
        else:
            self.tray_start_action.setEnabled(True)
            self.tray_stop_action.setEnabled(False)
            self.tray_status_action.setText("Status: ● Stopped")
            self.tray_icon.setToolTip("GoodByeDPI GUI - Stopped")

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def full_exit(self):
        if self.is_running:
            self.stop_goodbyedpi()
        self.settings.setValue("geometry", self.saveGeometry())
        self.tray_icon.hide()
        QApplication.quit()

    # ------------------------------------------------------------------
    # Log
    # ------------------------------------------------------------------
    @Slot(str)
    def append_log(self, text: str):
        self.log_view.append(text)

    # ------------------------------------------------------------------
    # Update check
    # ------------------------------------------------------------------
    def check_for_updates(self):
        try:
            req = urllib.request.Request(
                RELEASES_LATEST_URL,
                headers={"User-Agent": "Mozilla/5.0 GoodByeDPI-GUI-Updater"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                final_url = response.url

            m = re.search(r"/tag/[vV]?([0-9]+(?:\.[0-9]+)*)", final_url)
            if not m:
                return
            latest_version = m.group(1)
            if self.is_newer_version(latest_version):
                self.update_found_signal.emit(latest_version)
        except Exception:
            pass  # Silent fail (offline, DNS, etc.)

    @staticmethod
    def _parse_version(v: str):
        try:
            return tuple(int(p) for p in v.split("."))
        except Exception:
            return None

    def is_newer_version(self, remote_version: str) -> bool:
        cur = self._parse_version(CURRENT_VERSION)
        rem = self._parse_version(remote_version)
        if cur is None or rem is None:
            return False
        return rem > cur

    @Slot(str)
    def show_update_notification(self, new_version: str):
        box = QMessageBox(self)
        box.setWindowTitle("Update Available")
        box.setIcon(QMessageBox.Information)
        box.setText(
            f"A new version of GoodByeDPI GUI is available!\n\n"
            f"Current version:  v{CURRENT_VERSION}\n"
            f"Latest version:   v{new_version}\n\n"
            f"Do you want to open the Releases page?"
        )
        ok_btn = box.addButton("Later", QMessageBox.RejectRole)
        update_btn = box.addButton("Update", QMessageBox.AcceptRole)
        box.setDefaultButton(update_btn)
        box.exec()

        if box.clickedButton() is update_btn:
            QDesktopServices.openUrl(QUrl(RELEASES_URL))

    # ------------------------------------------------------------------
    # Window close behaviour
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        box = QMessageBox(self)
        box.setWindowTitle("Exit Options")
        box.setIcon(QMessageBox.Question)
        box.setText("What would you like to do?")
        exit_btn = box.addButton("Exit", QMessageBox.DestructiveRole)
        tray_btn = box.addButton("Minimize to Tray", QMessageBox.AcceptRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.RejectRole)
        box.setDefaultButton(cancel_btn)
        box.exec()

        if box.clickedButton() is exit_btn:
            event.accept()
            self.full_exit()
        elif box.clickedButton() is tray_btn:
            self.hide()
            self.tray_icon.show()
            event.ignore()
        else:
            event.ignore()


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not is_admin():
        QMessageBox.critical(
            None, "Administrator Required",
            "GoodByeDPI GUI must be run as Administrator.\n\n"
            "Right-click the app and choose 'Run as administrator'."
        )
        sys.exit(1)

    window = GoodbyeDPIManager()
    window.show()
    sys.exit(app.exec())