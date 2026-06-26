import sys
import os
import subprocess
import ctypes
import json
import urllib.request
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QLineEdit,
    QCheckBox, QMessageBox, QGroupBox, QMenu, QSystemTrayIcon
)
from PySide6.QtCore import Qt, QProcess, Signal, Slot, QSettings, QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QAction


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


DPI_EXE = resource_path("goodbyedpi.exe")

# 🔹 Current version of the GUI
CURRENT_VERSION = "1.0.2"
# آدرس صفحه‌ی عمومی (نه API) که به آخرین ریلیز ریدایرکت می‌شود
RELEASES_LATEST_URL = "https://github.com/ZvanTors/GoodByeDPI-GUI/releases/latest"
RELEASES_URL = "https://github.com/ZvanTors/GoodByeDPI-GUI/releases"


class GoodbyeDPIManager(QMainWindow):
    log_signal = Signal(str)
    update_found_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GoodByeDPI GUI")
        self.setWindowIcon(QIcon(resource_path("logo.ico")))
        self.resize(680, 480)

        self.process = None
        self.is_running = False

        # Settings
        self.settings = QSettings("GoodbyeDPIManager", "GUI")
        self.mode_index = self.settings.value("mode_index", 0, type=int)
        self.custom_args = self.settings.value("custom_args", "", type=str)

        # ---- System Tray ----
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(resource_path("logo.ico")))
        self.tray_icon.setToolTip("GoodByeDPI GUI - Stopped")

        self.tray_menu = QMenu()

        self.tray_start_action = QAction("▶ Start")
        self.tray_start_action.triggered.connect(self.start_goodbyedpi)
        self.tray_menu.addAction(self.tray_start_action)

        self.tray_stop_action = QAction("⏹ Stop")
        self.tray_stop_action.triggered.connect(self.stop_goodbyedpi)
        self.tray_stop_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_stop_action)

        self.tray_status_action = QAction("Status: ● Stopped")
        self.tray_status_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_status_action)

        self.tray_exit_action = QAction("Exit")
        self.tray_exit_action.triggered.connect(self.full_exit)
        self.tray_menu.addAction(self.tray_exit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Settings group ---
        settings_group = QGroupBox("DPI Circumvention Settings")
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["-6 (Recommended)", "-5 (General)", "Custom"])
        self.mode_combo.setCurrentIndex(self.mode_index)
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)

        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom arguments:"))
        self.custom_args_edit = QLineEdit(self.custom_args)
        self.custom_args_edit.setPlaceholderText("e.g. -f 2 -e 40 --native-frag --reverse-frag")
        custom_layout.addWidget(self.custom_args_edit)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        settings_layout.addLayout(custom_layout)

        self.autostart_check = QCheckBox("Run on Windows startup (Task Scheduler)")
        self.autostart_check.stateChanged.connect(self.toggle_autostart)
        settings_layout.addWidget(self.autostart_check)

        main_layout.addWidget(settings_group)

        # --- Controls ---
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.start_goodbyedpi)
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_goodbyedpi)
        self.status_label = QLabel("Status: ● Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # --- Output log ---
        log_group = QGroupBox("Output")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("font-family: Consolas, monospace; font-size: 9pt;")
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # --- Bottom bar: version on left, credit on right ---
        bottom_layout = QHBoxLayout()
        self.version_label = QLabel(f"V{CURRENT_VERSION}")
        self.version_label.setStyleSheet("color: #888; font-size: 9pt; padding: 2px 6px;")
        bottom_layout.addWidget(self.version_label)
        bottom_layout.addStretch()
        credit_label = QLabel("Made with ❤️ by AmooReza (WhiteDNS)")
        credit_label.setStyleSheet("color: #aaa; font-size: 8pt; padding: 2px 6px;")
        bottom_layout.addWidget(credit_label)
        main_layout.addLayout(bottom_layout)

        # Connect signals
        self.log_signal.connect(self.append_log)
        self.update_found_signal.connect(self.show_update_notification)

        # Initial UI state
        self.update_autostart_check()
        self.on_mode_changed()
        self.update_tray_status()

        # --- Check for updates in background ---
        threading.Thread(target=self.check_for_updates, daemon=True).start()

    # ---- Autostart ----
    def is_autostart_enabled(self):
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/tn", "GoodbyeDPIManager"],
                capture_output=True, text=True
            )
            return "GoodbyeDPIManager" in result.stdout
        except:
            return False

    def update_autostart_check(self):
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(self.is_autostart_enabled())
        self.autostart_check.blockSignals(False)

    def toggle_autostart(self, state):
        if state:
            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
            task_name = "GoodbyeDPIManager"
            subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], capture_output=True)
            try:
                subprocess.run(
                    ["schtasks", "/create", "/tn", task_name,
                     "/tr", f'"{exe_path}"', "/sc", "onlogon", "/rl", "highest", "/f"],
                    capture_output=True, check=True
                )
                QMessageBox.information(self, "Success", "Task created successfully.")
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Error", f"Failed to create task:\n{e.stderr}")
        else:
            try:
                subprocess.run(
                    ["schtasks", "/delete", "/tn", "GoodbyeDPIManager", "/f"],
                    capture_output=True, check=True
                )
                QMessageBox.information(self, "Success", "Task removed.")
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Error", f"Failed to remove task:\n{e.stderr}")
        self.update_autostart_check()

    # ---- Mode ----
    def on_mode_changed(self):
        custom = self.mode_combo.currentIndex() == 2
        self.custom_args_edit.setEnabled(custom)
        if not custom:
            self.custom_args_edit.clear()

    # ---- Start/Stop ----
    def start_goodbyedpi(self):
        if self.is_running:
            return

        self.settings.setValue("mode_index", self.mode_combo.currentIndex())
        self.settings.setValue("custom_args", self.custom_args_edit.text())

        args = []
        idx = self.mode_combo.currentIndex()
        if idx == 0:
            args = ["-6"]
        elif idx == 1:
            args = ["-5"]
        else:
            custom = self.custom_args_edit.text().strip()
            if custom:
                args = custom.split()

        if not os.path.exists(DPI_EXE):
            QMessageBox.critical(self, "Error", f"GoodbyeDPI executable not found:\n{DPI_EXE}")
            return

        try:
            self.process = QProcess(self)
            self.process.setProgram(DPI_EXE)
            self.process.setArguments(args)
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.finished.connect(self.on_process_finished)
            self.process.start()

            if not self.process.waitForStarted(3000):
                QMessageBox.critical(self, "Error", "Failed to start. Run as Administrator!")
                return

            self.is_running = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Status: ● Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.log_signal.emit("--- GoodbyeDPI started ---")
            self.update_tray_status()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error:\n{e}")

    def stop_goodbyedpi(self):
        if self.process and self.is_running:
            self.process.kill()
            self.process.waitForFinished(2000)
            self.is_running = False
            self.on_process_finished()
            self.update_tray_status()

    def handle_output(self):
        data = self.process.readAllStandardOutput()
        if data:
            text = str(data, encoding='utf-8', errors='replace')
            self.log_signal.emit(text)

    def on_process_finished(self):
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: ● Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        self.log_signal.emit("--- GoodbyeDPI stopped ---")
        self.update_tray_status()

    def update_tray_status(self):
        """هم‌راستا کردن منوی آیکون سینی با وضعیت فعلی"""
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
        """بازگرداندن پنجره با دوبار کلیک روی آیکون سینی"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def full_exit(self):
        """خروج کامل: توقف GoodbyeDPI و بستن برنامه"""
        if self.is_running:
            self.stop_goodbyedpi()
        self.tray_icon.hide()
        QApplication.quit()

    @Slot(str)
    def append_log(self, text):
        self.log_view.append(text)

    # ---- Update checking (new method using redirect) ----
    def check_for_updates(self):
        """Check for updates by following the /releases/latest redirect on GitHub."""
        try:
            req = urllib.request.Request(RELEASES_LATEST_URL, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            # با urlopen ریدایرکت‌ها دنبال می‌شود و response.url آدرس نهایی را می‌دهد
            with urllib.request.urlopen(req, timeout=10) as response:
                final_url = response.url  # e.g. https://github.com/.../releases/tag/V1.0.2
            # استخراج تگ از انتهای آدرس
            tag = final_url.rstrip("/").split("/")[-1]   # V1.0.2 یا v1.0.2
            latest_version = tag.lstrip("v").lstrip("V") # 1.0.2
            if latest_version and self.is_newer_version(latest_version):
                self.update_found_signal.emit(latest_version)
        except Exception:
            # در صورت خطا (مثل اینترنت قطع) بی‌صدا رد شو
            pass

    def is_newer_version(self, remote_version):
        try:
            current = tuple(map(int, CURRENT_VERSION.split(".")))
            remote = tuple(map(int, remote_version.split(".")))
            return remote > current
        except:
            return False

    @Slot(str)
    def show_update_notification(self, new_version):
        """Show a message box with OK and Update buttons."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Update Available")
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(
            f"A new version of GoodByeDPI GUI is available!\n\n"
            f"Current version: V{CURRENT_VERSION}\n"
            f"Latest version: V{new_version}\n\n"
            f"Do you want to visit the Releases page?"
        )
        ok_btn = msg_box.addButton("OK", QMessageBox.RejectRole)
        update_btn = msg_box.addButton("Update", QMessageBox.AcceptRole)
        msg_box.setDefaultButton(update_btn)
        msg_box.exec()

        if msg_box.clickedButton() == update_btn:
            QDesktopServices.openUrl(QUrl(RELEASES_URL))

    # ---- Window close (X button) ----
    def closeEvent(self, event):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Exit Options")
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setText("What would you like to do?")
        exit_btn = msg_box.addButton("Exit", QMessageBox.DestructiveRole)
        tray_btn = msg_box.addButton("Minimize to Tray", QMessageBox.AcceptRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.RejectRole)
        msg_box.setDefaultButton(cancel_btn)
        msg_box.exec()

        if msg_box.clickedButton() == exit_btn:
            self.full_exit()
            event.accept()
        elif msg_box.clickedButton() == tray_btn:
            self.hide()
            self.tray_icon.show()
            event.ignore()
        else:
            event.ignore()


if __name__ == "__main__":
    if not ctypes.windll.shell32.IsUserAnAdmin():
        QMessageBox.critical(None, "Error", "This program must be run as Administrator!")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = GoodbyeDPIManager()
    window.show()
    sys.exit(app.exec())