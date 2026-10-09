"""Pure UI for GoodByeDPI GUI. Exposes signals for user actions."""
import time

from PySide6.QtCore import (
    Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import (
    QIcon, QColor, QPainter, QTextCursor, QTextCharFormat,
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QComboBox, QLineEdit, QCheckBox,
    QGroupBox, QFrame, QSizePolicy, QApplication, QLayout,
    QGraphicsOpacityEffect,
)

from constants import APP_VERSION, MODE_PRESETS
from theme import DARK_QSS
from utils import resource_path


# ------------------------------------------------------------------
# Animated status dot
# ------------------------------------------------------------------
class _StatusDot(QWidget):
    """A small colored dot that can pulse when active."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color = QColor("#f38ba8")

        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(1.0)
        self.setGraphicsEffect(self._effect)

        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(1400)
        self._anim.setStartValue(1.0)
        self._anim.setKeyValueAt(0.5, 0.30)
        self._anim.setEndValue(1.0)
        self._anim.setLoopCount(-1)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)

    def set_color(self, color_hex: str) -> None:
        self._color = QColor(color_hex)
        self.update()

    def start_pulse(self) -> None:
        if self._anim.state() != QPropertyAnimation.Running:
            self._anim.start()

    def stop_pulse(self) -> None:
        self._anim.stop()
        self._effect.setOpacity(1.0)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(self._color)
        p.setPen(Qt.NoPen)
        p.drawEllipse(self.rect())


# ------------------------------------------------------------------
# Status pill (dot + text)
# ------------------------------------------------------------------
class _StatusPill(QFrame):
    """Rounded pill combining the animated dot with a status label."""

    _STATE = {
        "stopped": ("#f38ba8", "rgba(243, 139, 168, 0.12)",
                    "rgba(243, 139, 168, 0.35)", "Stopped"),
        "running": ("#a6e3a1", "rgba(166, 227, 161, 0.12)",
                    "rgba(166, 227, 161, 0.35)", "Running"),
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusPill")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 16, 6)
        layout.setSpacing(8)

        self._dot = _StatusDot()
        self._label = QLabel("Stopped")
        self._label.setObjectName("statusText")

        layout.addWidget(self._dot)
        layout.addWidget(self._label)

        self.set_state("stopped")

    def set_state(self, state: str) -> None:
        color, bg, border, text = self._STATE.get(state, self._STATE["stopped"])
        self._dot.set_color(color)
        self._label.setText(text)

        if state == "running":
            self._dot.start_pulse()
        else:
            self._dot.stop_pulse()

        self.setStyleSheet(f"""
            QFrame#statusPill {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QFrame#statusPill QLabel {{
                color: {color};
                background: transparent;
                font-weight: 700;
                font-size: 9.5pt;
            }}
        """)


# ------------------------------------------------------------------
# Uptime chip (⏱ 00:00:00)
# ------------------------------------------------------------------
class _UptimeChip(QFrame):
    """A small chip showing how long GoodbyeDPI has been running."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("uptimeChip")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setVisible(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 16, 6)
        layout.setSpacing(8)

        icon = QLabel("⏱")
        icon.setObjectName("uptimeIcon")

        self._label = QLabel("00:00:00")
        self._label.setObjectName("uptimeText")

        layout.addWidget(icon)
        layout.addWidget(self._label)

        self._start_time: float = 0.0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        self.setStyleSheet("""
            QFrame#uptimeChip {
                background-color: rgba(137, 180, 250, 0.10);
                border: 1px solid rgba(137, 180, 250, 0.30);
                border-radius: 12px;
            }
            QFrame#uptimeChip QLabel { background: transparent; }
            QLabel#uptimeIcon { color: #89b4fa; font-size: 10pt; }
            QLabel#uptimeText {
                color: #a6adc8;
                font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
                font-size: 9.5pt;
                font-weight: 700;
                letter-spacing: 0.5px;
            }
        """)

    def start(self) -> None:
        self._start_time = time.monotonic()
        self._label.setText("00:00:00")
        self.setVisible(True)
        self._timer.start()

    def stop_and_hide(self) -> None:
        self._timer.stop()
        self.setVisible(False)

    def _tick(self) -> None:
        elapsed = int(time.monotonic() - self._start_time)
        if elapsed < 0:
            elapsed = 0
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self._label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


# ------------------------------------------------------------------
# Main window
# ------------------------------------------------------------------
class MainWindow(QMainWindow):
    """The main application window (UI only, no business logic)."""

    # User-action signals
    start_clicked            = Signal()
    stop_clicked             = Signal()
    mode_changed             = Signal(int)
    custom_args_changed      = Signal(str)
    autostart_toggled        = Signal(bool)
    close_choice             = Signal(str)
    check_update_clicked     = Signal()
    clear_log_clicked        = Signal()
    copy_log_clicked         = Signal()
    about_clicked            = Signal()
    custom_args_help_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GoodByeDPI GUI")
        self.setWindowIcon(QIcon(resource_path("logo.ico")))
        self.setStyleSheet(DARK_QSS)

        screen = QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            w = min(880, int(avail.width() * 0.62))
            h = min(720, int(avail.height() * 0.78))
            self.resize(max(w, 700), max(h, 600))
        else:
            self.resize(880, 700)

        self.setMinimumSize(680, 580)

        self._build_ui()
        self._wire_internal_signals()

    # ------------------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        self._apply_dark_titlebar()

    def _apply_dark_titlebar(self) -> None:
        try:
            import ctypes
            hwnd = int(self.winId())
            value = ctypes.c_int(1)
            size = ctypes.sizeof(value)
            for attr in (20, 19):
                res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, attr, ctypes.byref(value), size
                )
                if res == 0:
                    break
        except Exception:
            pass

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(22, 22, 22, 18)
        root.setSpacing(14)

        header = self._build_header()
        header.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        root.addWidget(header)

        self._settings_group = self._build_settings_group()
        self._settings_group.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Minimum
        )
        root.addWidget(self._settings_group)

        root.addLayout(self._build_controls())

        log_group = self._build_log_group()
        log_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        root.addWidget(log_group, 1)

        root.addLayout(self._build_footer())

        self.set_running_state(False)

    # ------------------------------------------------------------------
    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("headerFrame")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(22, 14, 22, 14)
        layout.setSpacing(14)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        text_col.setContentsMargins(0, 0, 0, 0)

        title = QLabel("🛡  GoodByeDPI GUI")
        title.setObjectName("appTitle")

        subtitle = QLabel("Bypass Deep Packet Inspection on Windows")
        subtitle.setObjectName("appSubtitle")

        text_col.addWidget(title)
        text_col.addWidget(subtitle)

        layout.addLayout(text_col, 1)

        badge = QPushButton(f"v{APP_VERSION}")
        badge.setObjectName("versionBadge")
        badge.setCursor(Qt.PointingHandCursor)
        badge.setToolTip("About GoodByeDPI GUI")
        badge.clicked.connect(self.about_clicked.emit)
        layout.addWidget(badge, 0, Qt.AlignVCenter)

        return header

    # ------------------------------------------------------------------
    def _build_settings_group(self) -> QGroupBox:
        group = QGroupBox("DPI Circumvention Settings")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 14, 18, 18)
        layout.setSpacing(14)
        layout.setSizeConstraint(QLayout.SetMinimumSize)

        # ---- Mode row ----
        mode_row = QHBoxLayout()
        mode_row.setSpacing(14)

        mode_label = QLabel("Mode")
        mode_label.setObjectName("fieldLabel")
        mode_label.setFixedWidth(140)

        self.mode_combo = QComboBox()
        for label, _args, tooltip in MODE_PRESETS:
            self.mode_combo.addItem(label)
            self.mode_combo.setItemData(
                self.mode_combo.count() - 1, tooltip, Qt.ToolTipRole
            )
        self.mode_combo.currentIndexChanged.connect(self._refresh_mode_tooltip)
        self._refresh_mode_tooltip()

        mode_row.addWidget(mode_label)
        mode_row.addWidget(self.mode_combo, 1)
        layout.addLayout(mode_row)

        # ---- Custom args row (in a transparent container) ----
        self._custom_args_container = QWidget()
        self._custom_args_container.setObjectName("customArgsContainer")
        self._custom_args_container.setAttribute(Qt.WA_StyledBackground, True)

        container_layout = QVBoxLayout(self._custom_args_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(6)

        # --- Top row: label + edit + help button ---
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(14)

        custom_label = QLabel("Custom arguments")
        custom_label.setObjectName("fieldLabel")
        custom_label.setFixedWidth(140)

        self.custom_args_edit = QLineEdit()
        self.custom_args_edit.setPlaceholderText(
            "e.g.  -f 2 -e 40 --native-frag --reverse-frag"
        )

        self.custom_args_help_btn = QPushButton("?")
        self.custom_args_help_btn.setObjectName("helpBtn")
        self.custom_args_help_btn.setCursor(Qt.PointingHandCursor)
        self.custom_args_help_btn.setFixedSize(40, 36)
        self.custom_args_help_btn.setToolTip("Show available arguments")

        top_row.addWidget(custom_label)
        top_row.addWidget(self.custom_args_edit, 1)
        top_row.addWidget(self.custom_args_help_btn, 0)
        container_layout.addLayout(top_row)

        # --- Validation status row (indented to match the edit field) ---
        self._args_validation_label = QLabel("")
        self._args_validation_label.setObjectName("argsValidation")
        self._args_validation_label.setMinimumHeight(16)
        self._args_validation_label.setWordWrap(False)
        self._args_validation_label.setTextInteractionFlags(
            Qt.NoTextInteraction
        )

        status_row = QHBoxLayout()
        status_row.setContentsMargins(154, 0, 0, 0)   # 140 label + 14 spacing
        status_row.setSpacing(0)
        status_row.addWidget(self._args_validation_label, 1)
        container_layout.addLayout(status_row)

        layout.addWidget(self._custom_args_container)

        # ---- Autostart checkbox ----
        self.autostart_check = QCheckBox(
            "Run on Windows startup  (Task Scheduler)"
        )
        layout.addSpacing(2)
        layout.addWidget(self.autostart_check)

        # Hide custom args by default (Fast mode)
        self._custom_args_container.setVisible(False)

        return group

    # ------------------------------------------------------------------
    def _refresh_mode_tooltip(self) -> None:
        idx = self.mode_combo.currentIndex()
        if 0 <= idx < len(MODE_PRESETS):
            self.mode_combo.setToolTip(MODE_PRESETS[idx][2])

    # ------------------------------------------------------------------
    def _build_controls(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.setMinimumWidth(130)

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.setMinimumWidth(130)
        self.stop_btn.setEnabled(False)

        self._status = _StatusPill()
        self._uptime = _UptimeChip()

        row.addWidget(self.start_btn)
        row.addWidget(self.stop_btn)
        row.addSpacing(10)
        row.addWidget(self._status)
        row.addWidget(self._uptime)
        row.addStretch()
        return row

    # ------------------------------------------------------------------
    def _build_log_group(self) -> QGroupBox:
        group = QGroupBox("Output")

        layout = QVBoxLayout(group)
        layout.setContentsMargins(18, 14, 18, 18)
        layout.setSpacing(12)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(120)
        self.log_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.log_view, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        self.clear_log_btn = QPushButton("Clear")
        self.clear_log_btn.setObjectName("smallBtn")

        self.copy_log_btn = QPushButton("Copy")
        self.copy_log_btn.setObjectName("smallBtn")

        btn_row.addWidget(self.clear_log_btn)
        btn_row.addWidget(self.copy_log_btn)
        layout.addLayout(btn_row)

        return group

    # ------------------------------------------------------------------
    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(12)

        self.check_update_btn = QPushButton("🔄  Check for updates")
        self.check_update_btn.setObjectName("updateBtn")
        self.check_update_btn.setCursor(Qt.PointingHandCursor)
        self.check_update_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        credit = self._build_credit_badge()

        row.addWidget(self.check_update_btn, 0, Qt.AlignVCenter)
        row.addStretch()
        row.addWidget(credit, 0, Qt.AlignVCenter)
        return row

    # ------------------------------------------------------------------
    def _build_credit_badge(self) -> QFrame:
        badge = QFrame()
        badge.setObjectName("creditBadge")
        badge.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        layout = QHBoxLayout(badge)
        layout.setContentsMargins(14, 5, 16, 5)
        layout.setSpacing(6)

        heart = QLabel("❤")
        heart.setObjectName("creditHeart")

        made_with = QLabel("Made with")
        made_with.setObjectName("creditBy")

        author = QLabel("AmooReza")
        author.setObjectName("creditAuthor")

        dot = QLabel("·")
        dot.setObjectName("creditBy")

        brand = QLabel("WhiteDNS")
        brand.setObjectName("creditBrand")

        for w in (heart, made_with, author, dot, brand):
            layout.addWidget(w)

        return badge

    # ------------------------------------------------------------------
    def _wire_internal_signals(self) -> None:
        self.start_btn.clicked.connect(self.start_clicked.emit)
        self.stop_btn.clicked.connect(self.stop_clicked.emit)
        self.mode_combo.currentIndexChanged.connect(self.mode_changed.emit)
        self.mode_combo.currentIndexChanged.connect(self._refresh_mode_tooltip)
        self.custom_args_edit.textEdited.connect(self.custom_args_changed.emit)
        self.autostart_check.toggled.connect(self.autostart_toggled.emit)
        self.check_update_btn.clicked.connect(self.check_update_clicked.emit)
        self.clear_log_btn.clicked.connect(self.clear_log_clicked.emit)
        self.copy_log_btn.clicked.connect(self.copy_log_clicked.emit)
        self.custom_args_help_btn.clicked.connect(
            self.custom_args_help_clicked.emit
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def set_running_state(self, running: bool) -> None:
        if running:
            self._status.set_state("running")
            self._uptime.start()
        else:
            self._status.set_state("stopped")
            self._uptime.stop_and_hide()
        self.start_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def set_mode_index(self, idx: int) -> None:
        idx = max(0, min(idx, self.mode_combo.count() - 1))
        self.mode_combo.blockSignals(True)
        self.mode_combo.setCurrentIndex(idx)
        self.mode_combo.blockSignals(False)
        self._refresh_mode_tooltip()

    def set_custom_args(self, text: str) -> None:
        self.custom_args_edit.setText(text)

    def set_autostart(self, enabled: bool) -> None:
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(enabled)
        self.autostart_check.blockSignals(False)

    def set_custom_args_visible(self, visible: bool) -> None:
        """Show or hide the Custom-arguments row and force a relayout."""
        self._custom_args_container.setVisible(visible)
        self._custom_args_container.updateGeometry()
        self._settings_group.updateGeometry()
        self._settings_group.adjustSize()
        self.updateGeometry()

    # ------------------------------------------------------------------
    def set_args_validation(self, errors: list[str],
                            warnings: list[str]) -> None:
        """Update the validation status line under the custom args field.

        - Red   ✕ : errors found
        - Yellow ⚠ : warnings only
        - Green  ✓ : all good (only when there is input)
        - Hidden  : empty input
        """
        lbl = self._args_validation_label
        args_empty = not self.custom_args_edit.text().strip()

        if errors:
            first = errors[0]
            extra = len(errors) - 1
            summary = first + (f"   (+{extra} more)" if extra > 0 else "")
            lbl.setText(f"✕  {summary}")
            lbl.setStyleSheet(
                "color:#f38ba8; font-size:9pt; font-weight:600;"
                " background:transparent;"
            )
            tip_lines = [f"✕  {e}" for e in errors] + \
                        [f"⚠  {w}" for w in warnings]
            lbl.setToolTip("\n".join(tip_lines))

        elif warnings:
            first = warnings[0]
            extra = len(warnings) - 1
            summary = first + (f"   (+{extra} more)" if extra > 0 else "")
            lbl.setText(f"⚠  {summary}")
            lbl.setStyleSheet(
                "color:#f9e2af; font-size:9pt; font-weight:600;"
                " background:transparent;"
            )
            lbl.setToolTip("\n".join(f"⚠  {w}" for w in warnings))

        elif not args_empty:
            lbl.setText("✓  Arguments look valid")
            lbl.setStyleSheet(
                "color:#a6e3a1; font-size:9pt; font-weight:600;"
                " background:transparent;"
            )
            lbl.setToolTip("")

        else:
            lbl.setText("")
            lbl.setStyleSheet("")
            lbl.setToolTip("")

    # ------------------------------------------------------------------
    # Log with color coding
    # ------------------------------------------------------------------
    def append_log(self, text: str) -> None:
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)

        fmt = QTextCharFormat()
        low = text.lower()
        if "[error]" in low or "error" in low[:10]:
            fmt.setForeground(QColor("#f38ba8"))
        elif "[warn" in low or "warn" in low[:10]:
            fmt.setForeground(QColor("#f9e2af"))
        elif text.startswith("───"):
            fmt.setForeground(QColor("#89b4fa"))
        else:
            fmt.setForeground(QColor("#a6e3a1"))

        cursor.insertText(text + "\n", fmt)
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()

    def clear_log(self) -> None:
        self.log_view.clear()

    def copy_log(self) -> str:
        return self.log_view.toPlainText()

    def show_info(self, title: str, message: str) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, title, message)

    # ------------------------------------------------------------------
    # Window close behaviour
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        from PySide6.QtWidgets import QMessageBox

        box = QMessageBox(self)
        box.setWindowTitle("Exit Options")
        box.setIcon(QMessageBox.Question)
        box.setText("What would you like to do?")
        exit_btn = box.addButton("Exit", QMessageBox.DestructiveRole)
        tray_btn = box.addButton("Minimize to Tray", QMessageBox.AcceptRole)
        cancel_btn = box.addButton("Cancel", QMessageBox.RejectRole)
        box.setDefaultButton(cancel_btn)
        box.exec()

        clicked = box.clickedButton()
        if clicked is exit_btn:
            self.close_choice.emit("exit")
            event.accept()
        elif clicked is tray_btn:
            self.close_choice.emit("tray")
            event.ignore()
        else:
            self.close_choice.emit("cancel")
            event.ignore()