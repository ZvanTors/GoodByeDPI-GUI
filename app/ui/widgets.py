"""Reusable custom widgets (status indicators, uptime, mode cards, toasts)."""
import time

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QObject, Signal, QEvent, Property, QParallelAnimationGroup,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QSizePolicy, QGraphicsOpacityEffect, QPushButton,
)


# ==================================================================
# Animated status dot
# ==================================================================
class StatusDot(QWidget):
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


# ==================================================================
# Status pill (dot + text)
# ==================================================================
class StatusPill(QFrame):
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

        self._dot = StatusDot()
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


# ==================================================================
# Uptime chip (⏱ 00:00:00)
# ==================================================================
_QWIDGETSIZE_MAX = 16777215  # Qt's internal QWIDGETSIZE_MAX


class UptimeChip(QFrame):
    """A small chip showing how long GoodbyeDPI has been running.

    V14 / I10: instead of appearing instantly with setVisible(), the chip
    fades + slides in over ~220 ms when running starts, and fades out
    when stopping. This keeps the footer layout from jumping.
    """

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

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity)

        self._anim_group: QParallelAnimationGroup | None = None

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

    # ------------------------------------------------------------------
    def start(self) -> None:
        self._start_time = time.monotonic()
        self._label.setText("00:00:00")
        self._timer.start()
        self._animate_in()

    def stop_and_hide(self) -> None:
        self._timer.stop()
        self._animate_out()

    def _tick(self) -> None:
        elapsed = int(time.monotonic() - self._start_time)
        if elapsed < 0:
            elapsed = 0
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self._label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    # ------------------------------------------------------------------
    def _stop_current_anim(self) -> None:
        if self._anim_group is not None:
            try:
                self._anim_group.stop()
            except RuntimeError:
                pass

    def _animate_in(self) -> None:
        self._stop_current_anim()

        self.setMaximumWidth(_QWIDGETSIZE_MAX)
        target_w = max(self.sizeHint().width(), 80)

        self.setVisible(True)
        self.setMaximumWidth(0)
        self._opacity.setOpacity(0.0)

        w_anim = QPropertyAnimation(self, b"maximumWidth", self)
        w_anim.setDuration(220)
        w_anim.setStartValue(0)
        w_anim.setEndValue(target_w)
        w_anim.setEasingCurve(QEasingCurve.OutCubic)

        o_anim = QPropertyAnimation(self._opacity, b"opacity", self)
        o_anim.setDuration(220)
        o_anim.setStartValue(0.0)
        o_anim.setEndValue(1.0)

        group = QParallelAnimationGroup(self)
        group.addAnimation(w_anim)
        group.addAnimation(o_anim)
        group.finished.connect(self._on_anim_in_done)
        self._anim_group = group
        group.start()

    def _on_anim_in_done(self) -> None:
        self.setMaximumWidth(_QWIDGETSIZE_MAX)

    def _animate_out(self) -> None:
        self._stop_current_anim()

        current_w = max(self.width(), 1)

        w_anim = QPropertyAnimation(self, b"maximumWidth", self)
        w_anim.setDuration(180)
        w_anim.setStartValue(current_w)
        w_anim.setEndValue(0)
        w_anim.setEasingCurve(QEasingCurve.InCubic)

        o_anim = QPropertyAnimation(self._opacity, b"opacity", self)
        o_anim.setDuration(180)
        o_anim.setStartValue(self._opacity.opacity())
        o_anim.setEndValue(0.0)

        group = QParallelAnimationGroup(self)
        group.addAnimation(w_anim)
        group.addAnimation(o_anim)
        group.finished.connect(self._on_anim_out_done)
        self._anim_group = group
        group.start()

    def _on_anim_out_done(self) -> None:
        self.setVisible(False)
        self.setMaximumWidth(_QWIDGETSIZE_MAX)


# ==================================================================
# Mode selection — cards instead of a ComboBox
# ==================================================================
class ModeCard(QFrame):
    """A single selectable card representing a DPI mode preset.

    Interaction is gated by an internal `_interactive` flag instead of
    Qt's enabled state, because ``setEnabled(False)`` causes Qt to
    repaint QSS-styled widgets with a de-saturated disabled palette —
    which we do not want here. The cards should look *identical* in
    both states; only clicks are blocked while a session is running.
    """

    clicked = Signal(str)

    def __init__(
        self,
        key: str,
        title: str,
        badge: str,
        icon: str,
        description: str,
        tooltip: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self._key = key
        self._selected = False
        self._interactive = True

        self.setObjectName("modeCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(84)
        if tooltip:
            self.setToolTip(tooltip)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setObjectName("modeCardIcon")
        self._icon_lbl.setFixedWidth(34)
        self._icon_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("modeCardTitle")
        self._title_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(6)
        title_row.addWidget(self._title_lbl)

        if badge:
            self._badge_lbl = QLabel(badge.upper())
            self._badge_lbl.setObjectName("modeCardBadge")
            self._badge_lbl.setAttribute(
                Qt.WA_TransparentForMouseEvents, True
            )
            title_row.addWidget(self._badge_lbl)

        title_row.addStretch()

        self._desc_lbl = QLabel(description)
        self._desc_lbl.setObjectName("modeCardDesc")
        self._desc_lbl.setWordWrap(True)
        self._desc_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(4)
        text_col.addLayout(title_row)
        text_col.addWidget(self._desc_lbl)
        text_col.addStretch()

        layout.addWidget(self._icon_lbl, 0, Qt.AlignTop)
        layout.addLayout(text_col, 1)

    # ------------------------------------------------------------------
    @property
    def key(self) -> str:
        return self._key

    def is_selected(self) -> bool:
        return self._selected

    def set_selected(self, selected: bool) -> None:
        if self._selected == selected:
            return
        self._selected = selected
        self.setProperty("selected", selected)
        self.style().unpolish(self)
        self.style().polish(self)

    # ------------------------------------------------------------------
    def set_interactive(self, interactive: bool) -> None:
        """Enable or disable click handling without touching QSS colors."""
        self._interactive = interactive
        self.setCursor(
            Qt.PointingHandCursor if interactive else Qt.ArrowCursor
        )

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if not self._interactive:
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self._key)
        super().mousePressEvent(event)


class ModeCardGroup(QWidget):
    """Horizontal group of `ModeCard`s with radio-button behaviour."""

    mode_changed = Signal(int)

    def __init__(self, presets, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._cards: list[ModeCard] = []

        for idx, p in enumerate(presets):
            card = ModeCard(
                key=p.key,
                title=p.title,
                badge=p.badge,
                icon=p.icon,
                description=p.description,
                tooltip=p.tooltip,
            )
            card.clicked.connect(lambda _key, i=idx: self.set_current_index(i))
            self._cards.append(card)
            layout.addWidget(card, 1)

        self._current = -1
        if self._cards:
            self.set_current_index(0, emit=False)

    def current_index(self) -> int:
        return self._current

    def set_current_index(self, idx: int, emit: bool = True) -> None:
        if not self._cards:
            return
        idx = max(0, min(idx, len(self._cards) - 1))
        changed = (idx != self._current)
        if changed:
            for i, card in enumerate(self._cards):
                card.set_selected(i == idx)
            self._current = idx
        if changed and emit:
            self.mode_changed.emit(idx)

    # ------------------------------------------------------------------
    def set_interactive(self, interactive: bool) -> None:
        """Block or allow clicks on every card without repainting colors."""
        for card in self._cards:
            card.set_interactive(interactive)


# ==================================================================
# In-app toast notifications
# ==================================================================
class Toast(QFrame):
    """A small, self-dismissing notification card.

    I4: includes an explicit close (×) button in addition to
    click-anywhere-to-dismiss.
    """

    dismissed = Signal(object)

    _KINDS = {
        "info":    ("ℹ", "#89b4fa", "rgba(137, 180, 250, 0.55)"),
        "success": ("✓", "#a6e3a1", "rgba(166, 227, 161, 0.55)"),
        "warning": ("⚠", "#f9e2af", "rgba(249, 226, 175, 0.55)"),
        "error":   ("✕", "#f38ba8", "rgba(243, 139, 168, 0.55)"),
    }

    def __init__(
        self,
        message: str,
        kind: str = "info",
        duration: int = 3500,
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setCursor(Qt.PointingHandCursor)

        icon_text, accent, border = self._KINDS.get(
            kind, self._KINDS["info"]
        )

        self.setStyleSheet(f"""
            QFrame#toast {{
                background-color: #1e1e2e;
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 10, 12)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon_text)
        icon_lbl.setStyleSheet(
            f"color:{accent}; font-size:13pt; font-weight:800;"
            " background:transparent;"
        )
        icon_lbl.setFixedWidth(18)
        icon_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        msg_lbl = QLabel(message)
        msg_lbl.setStyleSheet(
            "color:#cdd6f4; font-size:9.5pt; font-weight:500;"
            " background:transparent;"
        )
        msg_lbl.setWordWrap(True)

        close_btn = QPushButton("×")
        close_btn.setObjectName("toastClose")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setToolTip("Dismiss")
        close_btn.setStyleSheet("""
            QPushButton#toastClose {
                background-color: transparent;
                border: none;
                color: #6c7086;
                font-size: 13pt;
                font-weight: 700;
                padding: 0;
                min-width: 0;  max-width: 20px;
                min-height: 0; max-height: 20px;
            }
            QPushButton#toastClose:hover {
                color: #f38ba8;
            }
            QPushButton#toastClose:pressed {
                color: #eba0ac;
            }
        """)
        close_btn.clicked.connect(self.fade_out)

        layout.addWidget(icon_lbl, 0, Qt.AlignTop)
        layout.addWidget(msg_lbl, 1)
        layout.addWidget(close_btn, 0, Qt.AlignTop)

        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)

        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.finished.connect(self._on_anim_finished)

        self._duration = duration
        self._fading_out = False

    def show_animated(self) -> None:
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setDuration(220)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        QTimer.singleShot(self._duration, self._maybe_fade_out)

    def fade_out(self) -> None:
        if self._fading_out:
            return
        self._fading_out = True
        self._anim.stop()
        self._anim.setDuration(260)
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _maybe_fade_out(self) -> None:
        if not self._fading_out:
            self.fade_out()

    def _on_anim_finished(self) -> None:
        if self._fading_out:
            self.dismissed.emit(self)
            self.deleteLater()

    def mousePressEvent(self, event):
        # Click anywhere except the × button dismisses the toast.
        if event.button() == Qt.LeftButton:
            self.fade_out()
        super().mousePressEvent(event)


class ToastManager(QObject):
    """Positions and stacks `Toast` widgets at the bottom-right corner.

    V3: caps the number of simultaneously-visible toasts. When the limit
    is reached, the oldest toast is removed immediately to make room.
    """

    _MARGIN = 22
    _SPACING = 10
    _MAX_WIDTH = 340
    _MAX_TOASTS = 3

    def __init__(self, host: QWidget):
        super().__init__(host)
        self._host = host
        self._toasts: list[Toast] = []
        host.installEventFilter(self)

    def show(
        self,
        message: str,
        kind: str = "info",
        duration: int = 3500,
    ) -> None:
        self._enforce_limit()

        toast = Toast(message, kind, duration, self._host)
        toast.dismissed.connect(self._on_dismissed)

        max_w = min(
            self._MAX_WIDTH,
            max(240, self._host.width() - 2 * self._MARGIN - 20),
        )
        toast.setFixedWidth(max_w)
        toast.adjustSize()

        self._toasts.append(toast)
        toast.show_animated()
        self._reposition()

    # ------------------------------------------------------------------
    def _enforce_limit(self) -> None:
        """Remove the oldest toasts until we're below the limit."""
        while len(self._toasts) >= self._MAX_TOASTS:
            oldest = self._toasts.pop(0)
            try:
                oldest.dismissed.disconnect(self._on_dismissed)
            except (RuntimeError, TypeError):
                pass
            try:
                oldest.hide()
                oldest.setParent(None)
                oldest.deleteLater()
            except RuntimeError:
                pass

    # ------------------------------------------------------------------
    def _on_dismissed(self, toast: Toast) -> None:
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._reposition()

    def _reposition(self) -> None:
        if not self._toasts:
            return
        host_rect = self._host.rect()
        y_bottom = host_rect.height() - self._MARGIN

        for toast in reversed(self._toasts):
            h = toast.height()
            w = toast.width()
            x = host_rect.width() - w - self._MARGIN
            y = y_bottom - h
            toast.move(x, y)
            y_bottom = y - self._SPACING

    def eventFilter(self, obj, event):
        if obj is self._host and event.type() == QEvent.Resize:
            self._reposition()
        return super().eventFilter(obj, event)


# ==================================================================
# Animated button (Start / Stop)
# ==================================================================
class AnimatedButton(QPushButton):
    """QPushButton whose background colour animates between two palettes.

    ``setEnabled(False)`` fires the ``:disabled`` QSS rule instantly, so
    any colour animation would be cut off. This button keeps Qt's enabled
    state untouched and uses an internal ``_interactive`` flag to refuse
    clicks.
    """

    def __init__(
        self,
        text: str,
        active_hex: str,
        object_name: str = "",
        inactive_hex: str = "#1e1e2e",
        active_fg: str = "#11111b",
        inactive_fg: str = "#585b70",
        parent=None,
    ) -> None:
        super().__init__(text, parent)
        if object_name:
            self.setObjectName(object_name)

        self._active_hex = QColor(active_hex)
        self._inactive_hex = QColor(inactive_hex)
        self._active_fg = active_fg
        self._inactive_fg = inactive_fg

        self._current_bg = QColor(inactive_hex)
        self._current_fg = inactive_fg
        self._is_active = False
        self._interactive = False

        self._anim = QPropertyAnimation(self, b"animatedBg", self)
        self._anim.setDuration(260)
        self._anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.setCursor(Qt.ArrowCursor)
        self._refresh_style()

    # ------------------------------------------------------------------
    def _get_bg(self) -> QColor:
        return self._current_bg

    def _set_bg(self, color: QColor) -> None:
        self._current_bg = QColor(color)
        self._refresh_style()

    animatedBg = Property(QColor, _get_bg, _set_bg)

    # ------------------------------------------------------------------
    def _refresh_style(self) -> None:
        name = self.objectName()
        prefix = f"QPushButton#{name}" if name else "QPushButton"
        self.setStyleSheet(f"""
            {prefix} {{
                background-color: {self._current_bg.name()};
                color: {self._current_fg};
                border: none;
                border-radius: 9px;
                padding: 10px 22px;
                font-weight: 600;
                min-width: 100px;
                min-height: 20px;
            }}
            {prefix}:hover {{
                background-color: {self._current_bg.lighter(115).name()};
            }}
            {prefix}:pressed {{
                background-color: {self._current_bg.darker(120).name()};
            }}
        """)

    # ------------------------------------------------------------------
    def set_active(self, active: bool, animate: bool = True) -> None:
        """Switch between active (colored) and inactive (grey) palettes."""
        self._is_active = active
        self._interactive = active
        self._current_fg = self._active_fg if active else self._inactive_fg
        self.setCursor(
            Qt.PointingHandCursor if active else Qt.ArrowCursor
        )

        target = self._active_hex if active else self._inactive_hex

        if not animate or not self.isVisible():
            self._anim.stop()
            self._set_bg(target)
            return

        if (self._current_bg == target
                and self._anim.state() != QPropertyAnimation.Running):
            self._refresh_style()
            return

        self._anim.stop()
        self._anim.setStartValue(self._current_bg)
        self._anim.setEndValue(target)
        self._anim.start()

    def is_active(self) -> bool:
        return self._is_active

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        if not self._interactive:
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if not self._interactive:
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if not self._interactive:
            event.accept()
            return
        super().keyPressEvent(event)