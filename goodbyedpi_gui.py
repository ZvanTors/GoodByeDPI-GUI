import sys
import os
import subprocess
import ctypes
from PySide6.QtGui import QAction, QIcon

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QComboBox, QLineEdit,
    QCheckBox, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, QProcess, QTimer, Signal, Slot
from PySide6.QtGui import QAction

# برای بسته‌بندی PyInstaller
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# مسیر فایل اجرایی GoodbyeDPI (همراه بسته)
DPI_EXE = resource_path("goodbyedpi.exe")

class GoodbyeDPIManager(QMainWindow):
    log_signal = Signal(str)

    def __init__(self):
        super().__init__()
        icon_path = resource_path("logo.ico")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("GoodByeDPI GUI")
        self.resize(680, 480)

        self.process = None
        self.is_running = False

        # تنظیمات پایدار با QSettings
        from PySide6.QtCore import QSettings
        self.settings = QSettings("GoodbyeDPIManager", "GUI")
        self.load_settings()

        # ویجت مرکزی
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # === گروه تنظیمات ===
        settings_group = QGroupBox("DPI Circumvention Settings")
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)

        # انتخاب حالت
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["-6 (Recommended)", "-5 (General)", "Custom"])
        mode_layout.addWidget(self.mode_combo)
        settings_layout.addLayout(mode_layout)

        # پارامترهای دستی
        custom_layout = QHBoxLayout()
        custom_layout.addWidget(QLabel("Custom arguments:"))
        self.custom_args_edit = QLineEdit()
        self.custom_args_edit.setPlaceholderText("e.g. -f 2 -e 40 --native-frag --reverse-frag")
        custom_layout.addWidget(self.custom_args_edit)
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        settings_layout.addLayout(custom_layout)

        # اجرای خودکار با ویندوز (Task Scheduler)
        self.autostart_check = QCheckBox("Run on Windows startup (Task Scheduler)")
        self.autostart_check.stateChanged.connect(self.toggle_autostart)
        settings_layout.addWidget(self.autostart_check)

        main_layout.addWidget(settings_group)

        # === کنترل‌ها ===
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

        # === خروجی لاگ ===
        log_group = QGroupBox("Output")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("font-family: Consolas, monospace; font-size: 9pt;")
        log_layout.addWidget(self.log_view)
        main_layout.addWidget(log_group)

        # سیگنال لاگ
        self.log_signal.connect(self.append_log)

        # بارگذاری وضعیت اولیه
        self.update_ui_from_settings()
        self.on_mode_changed()

    # ---- تنظیمات با QSettings ----
    def load_settings(self):
        """بارگذاری تنظیمات ذخیره‌شده"""
        # حالت (0: -6, 1: -5, 2: custom)
        self.mode_index = self.settings.value("mode_index", 0, type=int)
        self.custom_args = self.settings.value("custom_args", "", type=str)
        # وضعیت autostart از Task Scheduler خوانده می‌شود، نه از QSettings

    def save_settings(self):
        """ذخیره تنظیمات فعلی"""
        self.settings.setValue("mode_index", self.mode_combo.currentIndex())
        self.settings.setValue("custom_args", self.custom_args_edit.text())

    def update_ui_from_settings(self):
        """اعمال تنظیمات به ویجت‌ها"""
        self.mode_combo.setCurrentIndex(self.mode_index)
        self.custom_args_edit.setText(self.custom_args)
        # به‌روزرسانی چک‌باکس autostart
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(self.is_autostart_enabled())
        self.autostart_check.blockSignals(False)

    # ---- منطق اجرای خودکار ----
    def is_autostart_enabled(self):
        try:
            result = subprocess.run(
                ["schtasks", "/query", "/tn", "GoodbyeDPIManager"],
                capture_output=True, text=True
            )
            return "GoodbyeDPIManager" in result.stdout
        except:
            return False

    def toggle_autostart(self, state):
        if state:
            # مسیر فایل اجرایی فعلی (در حالت بسته‌بندی sys.executable است)
            exe_path = sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]
            task_name = "GoodbyeDPIManager"
            # اگر قبلاً وظیفه‌ای وجود دارد، پاکش کن
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
                self.autostart_check.setChecked(False)
        else:
            try:
                subprocess.run(
                    ["schtasks", "/delete", "/tn", "GoodbyeDPIManager", "/f"],
                    capture_output=True, check=True
                )
                QMessageBox.information(self, "Success", "Task removed.")
            except subprocess.CalledProcessError as e:
                QMessageBox.critical(self, "Error", f"Failed to remove task:\n{e.stderr}")
        # به‌روزرسانی چک‌باکس بعد از تغییر واقعی
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(self.is_autostart_enabled())
        self.autostart_check.blockSignals(False)

    # ---- تغییر حالت ----
    def on_mode_changed(self):
        custom_mode = self.mode_combo.currentIndex() == 2
        self.custom_args_edit.setEnabled(custom_mode)
        if not custom_mode:
            self.custom_args_edit.clear()

    # ---- شروع/توقف ----
    def start_goodbyedpi(self):
        if self.is_running:
            return

        # ذخیره تنظیمات
        self.save_settings()

        # ساخت لیست آرگومان‌ها
        args = []
        mode_idx = self.mode_combo.currentIndex()
        if mode_idx == 0:
            args = ["-6"]
        elif mode_idx == 1:
            args = ["-5"]
        else:
            custom_text = self.custom_args_edit.text().strip()
            if custom_text:
                args = custom_text.split()

        # مسیر فایل اجرایی (داخل بسته)
        exe_path = DPI_EXE
        if not os.path.exists(exe_path):
            QMessageBox.critical(self, "Error", f"GoodbyeDPI executable not found:\n{exe_path}")
            return

        try:
            self.process = QProcess(self)
            self.process.setProgram(exe_path)
            self.process.setArguments(args)
            self.process.setProcessChannelMode(QProcess.MergedChannels)
            self.process.readyReadStandardOutput.connect(self.handle_output)
            self.process.finished.connect(self.on_process_finished)
            self.process.start()

            if not self.process.waitForStarted(3000):
                QMessageBox.critical(self, "Error", "Failed to start GoodbyeDPI. Make sure you have administrator rights.")
                return

            self.is_running = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Status: ● Running")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.log_signal.emit("--- GoodbyeDPI started ---")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error starting GoodbyeDPI:\n{e}")

    def stop_goodbyedpi(self):
        if self.process and self.is_running:
            self.process.kill()
            self.process.waitForFinished(2000)
            self.is_running = False
            self.on_process_finished()

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

    @Slot(str)
    def append_log(self, text):
        self.log_view.append(text)

    # ---- بستن برنامه ----
    def closeEvent(self, event):
        if self.is_running:
            reply = QMessageBox.question(self, "Confirm Exit",
                                         "GoodbyeDPI is running. Stop it and exit?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.stop_goodbyedpi()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    # بررسی دسترسی ادمین
    if not ctypes.windll.shell32.IsUserAnAdmin():
        QMessageBox.critical(None, "Error", "This program must be run as Administrator!")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = GoodbyeDPIManager()
    window.show()
    sys.exit(app.exec())