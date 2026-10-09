"""Pure UI for GoodByeDPI GUI. Exposes signals for user actions."""
from PySide6.QtCore import (
    Qt, Signal, QRect, QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import (
    QIcon, QColor, QTextCursor, QTextCharFormat,
)
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QLineEdit, QCheckBox,
    QGroupBox, QFrame, QSizePolicy, QApplication,
)

from app.constants import APP_VERSION, MODE_PRESETS, LOGO_ICO_REL
from app.ui.theme import DARK_QSS
from app.ui.widgets import (
    StatusPill, UptimeChip, ModeCardGroup, ToastManager,
)
from app.utils import resource_path


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
    donate_clicked           = Signal()
    clear_log_clicked        = Signal()
    copy_log_clicked         = Signal()
    about_clicked            = Signal()
    custom_args_help_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GoodByeDPI GUI")
        self.setWindowIcon(QIcon(resource_path(LOGO_ICO_REL)))
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

        # Animation handle for smooth height changes (kept as attribute
        # so Python doesn't garbage-collect it mid-flight).
        self._height_anim: QPropertyAnimation | None = None

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

        # Toast layer — children of the central widget, positioned manually.
        self._toast_manager = ToastManager(central)

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
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        # NOTE: We intentionally do NOT set SetMinimumSize here. That
        # constraint forced the group to always occupy its full sizeHint,
        # which pushed the group under the Start/Stop row as soon as the
        # Custom-arguments row appeared. The layout is now free to flex.

        # ---- Mode label ----
        mode_label = QLabel("Mode")
        mode_label.setObjectName("fieldLabel")
        layout.addWidget(mode_label)

        # ---- Mode cards ----
        self.mode_cards = ModeCardGroup(MODE_PRESETS)
        layout.addWidget(self.mode_cards)

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

        # --- Validation status row ---
        self._args_validation_label = QLabel("")
        self._args_validation_label.setObjectName("argsValidation")
        self._args_validation_label.setMinimumHeight(16)
        self._args_validation_label.setWordWrap(False)
        self._args_validation_label.setTextInteractionFlags(
            Qt.NoTextInteraction
        )

        status_row = QHBoxLayout()
        status_row.setContentsMargins(154, 0, 0, 0)
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

        self._status = StatusPill()
        self._uptime = UptimeChip()

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

        self.donate_btn = QPushButton("❤  Donate")
        self.donate_btn.setObjectName("donateBtn")
        self.donate_btn.setCursor(Qt.PointingHandCursor)
        self.donate_btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        credit = self._build_credit_badge()

        row.addWidget(self.check_update_btn, 0, Qt.AlignVCenter)
        row.addWidget(self.donate_btn, 0, Qt.AlignVCenter)
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
        self.mode_cards.mode_changed.connect(self.mode_changed.emit)
        self.custom_args_edit.textEdited.connect(self.custom_args_changed.emit)
        self.autostart_check.toggled.connect(self.autostart_toggled.emit)
        self.check_update_btn.clicked.connect(self.check_update_clicked.emit)
        self.donate_btn.clicked.connect(self.donate_clicked.emit)
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

    # --- Mode ---------------------------------------------------------
    def current_mode_index(self) -> int:
        return self.mode_cards.current_index()

    def set_mode_index(self, idx: int) -> None:
        self.mode_cards.set_current_index(idx, emit=False)

    # --- Custom args --------------------------------------------------
    def set_custom_args(self, text: str) -> None:
        self.custom_args_edit.setText(text)

    def set_autostart(self, enabled: bool) -> None:
        self.autostart_check.blockSignals(True)
        self.autostart_check.setChecked(enabled)
        self.autostart_check.blockSignals(False)

    # ------------------------------------------------------------------
    def set_custom_args_visible(
        self, visible: bool, animate: bool = True
    ) -> None:
        """Show or hide the Custom-arguments row.

        When `animate` is True and the window is on screen, the window
        height is smoothly adjusted so the new content fits without
        pushing into the Start/Stop row.

        When `animate` is False (e.g. during initial state restore),
        visibility is flipped and the window only grows if its current
        height is below the layout's minimum.
        """
        # isHidden() reflects the explicit "want to be visible" flag,
        # which is what we care about (isVisible() also returns False
        # when an ancestor is hidden, e.g. before the window is shown).
        currently_visible = not self._custom_args_container.isHidden()
        if currently_visible == visible:
            return

        central = self.centralWidget()
        if central is None:
            self._custom_args_container.setVisible(visible)
            return

        # Measure the layout's preferred height BEFORE the toggle.
        old_hint = central.sizeHint().height()

        self._custom_args_container.setVisible(visible)
        self._custom_args_container.updateGeometry()
        self._settings_group.updateGeometry()
        self.updateGeometry()

        # Force the layout engine to recompute synchronously.
        if central.layout() is not None:
            central.layout().activate()

        new_hint = central.sizeHint().height()
        delta = new_hint - old_hint

        if delta == 0:
            return

        if not animate:
            # Just make sure the window is not smaller than the minimum
            # required by the new content. Never shrink here — respect
            # whatever size the user had before.
            min_h = max(
                self.minimumHeight(),
                self.minimumSizeHint().height(),
            )
            if self.height() < min_h:
                self.resize(self.width(), min_h)
            return

        self._animate_height_delta(delta)

    # ------------------------------------------------------------------
    def _animate_height_delta(self, delta: int) -> None:
        """Smoothly change the window height by `delta` pixels."""
        if delta == 0:
            return
        if self.isMaximized() or self.isFullScreen():
            return

        # Determine the logical "base" height. If a height animation is
        # already running, trust its intended end value rather than the
        # current (mid-flight) geometry, so back-to-back toggles still
        # land on the correct final size.
        base_h = self.height()
        if self._height_anim is not None and \
                self._height_anim.state() == QPropertyAnimation.Running:
            end_val = self._height_anim.endValue()
            if isinstance(end_val, QRect):
                base_h = end_val.height()

        target_h = base_h + delta

        # Clamp to the screen.
        screen = self.screen() or QApplication.primaryScreen()
        if screen is not None:
            avail = screen.availableGeometry()
            max_h = max(self.minimumHeight(), avail.height() - 40)
            target_h = max(self.minimumHeight(), min(target_h, max_h))

        if target_h == base_h:
            return

        # If the window isn't on screen yet, snap directly (no animation).
        if not self.isVisible():
            self.resize(self.width(), target_h)
            return

        # Cancel any in-flight height animation before starting a new one.
        if self._height_anim is not None and \
                self._height_anim.state() == QPropertyAnimation.Running:
            self._height_anim.stop()

        start_geo = self.geometry()
        end_geo = QRect(
            start_geo.x(), start_geo.y(),
            start_geo.width(), target_h,
        )

        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(220)
        anim.setStartValue(start_geo)
        anim.setEndValue(end_geo)
        anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._height_anim = anim
        anim.start()

    # ------------------------------------------------------------------
    def set_args_validation(self, errors: list[str],
                            warnings: list[str]) -> None:
        """Update the validation status line under the custom args field."""
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

    # ------------------------------------------------------------------
    # Toast notifications
    # ------------------------------------------------------------------
    def show_toast(
        self,
        message: str,
        kind: str = "info",
        duration: int = 3500,
    ) -> None:
        """Show an in-app toast at the bottom-right of the window.

        kind: "info" | "success" | "warning" | "error"
        """
        self._toast_manager.show(message, kind, duration)

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