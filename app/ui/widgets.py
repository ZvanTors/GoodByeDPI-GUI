"""Reusable custom widgets (status indicators, uptime, mode cards, toasts)."""
import time

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    QObject, Signal, QEvent,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel,
    QSizePolicy, QGraphicsOpacityEffect,
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
class UptimeChip(QFrame):
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


# ==================================================================
# Mode selection — cards instead of a ComboBox
# ==================================================================
class ModeCard(QFrame):
    """A single selectable card representing a DPI mode preset.

    Emits `clicked` with its `key` when the user presses it.
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

        # --- Icon on the left ---
        self._icon_lbl = QLabel(icon)
        self._icon_lbl.setObjectName("modeCardIcon")
        self._icon_lbl.setFixedWidth(34)
        self._icon_lbl.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self._icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # --- Title row (title + optional badge) ---
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

        # --- Description ---
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
        # Force the QSS engine to re-evaluate selectors that depend on
        # the ancestor's "selected" property.
        self.style().unpolish(self)
        self.style().polish(self)
        for lbl in self.findChildren(QLabel):
            lbl.style().unpolish(lbl)
            lbl.style().polish(lbl)

    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
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

    # ------------------------------------------------------------------
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


# ==================================================================
# In-app toast notifications
# ==================================================================
class Toast(QFrame):
    """A small, self-dismissing notification card.

    Emits `dismissed` with itself once the fade-out finishes so the
    manager can remove it from its stack.
    """

    dismissed = Signal(object)

    _KINDS = {
        # kind:  (icon, accent, border)
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

        # Per-kind colours — we use an inline stylesheet because the
        # colour depends on `kind` at runtime and there is no easy way
        # to express that purely through the shared dark QSS.
        self.setStyleSheet(f"""
            QFrame#toast {{
                background-color: #1e1e2e;
                border: 1px solid {border};
                border-radius: 12px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

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

        layout.addWidget(icon_lbl, 0, Qt.AlignTop)
        layout.addWidget(msg_lbl, 1)

        # Fade animation
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)

        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.finished.connect(self._on_anim_finished)

        self._duration = duration
        self._fading_out = False

    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    def _maybe_fade_out(self) -> None:
        if not self._fading_out:
            self.fade_out()

    def _on_anim_finished(self) -> None:
        if self._fading_out:
            self.dismissed.emit(self)
            self.deleteLater()

    def mousePressEvent(self, event):
        # Click anywhere on the toast dismisses it immediately.
        if event.button() == Qt.LeftButton:
            self.fade_out()
        super().mousePressEvent(event)


class ToastManager(QObject):
    """Positions and stacks `Toast` widgets at the bottom-right corner."""

    _MARGIN = 22
    _SPACING = 10
    _MAX_WIDTH = 340

    def __init__(self, host: QWidget):
        super().__init__(host)
        self._host = host
        self._toasts: list[Toast] = []
        host.installEventFilter(self)

    # ------------------------------------------------------------------
    def show(
        self,
        message: str,
        kind: str = "info",
        duration: int = 3500,
    ) -> None:
        toast = Toast(message, kind, duration, self._host)
        toast.dismissed.connect(self._on_dismissed)

        # Clamp width so it fits the host even when the window is small.
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

    # ------------------------------------------------------------------
    def eventFilter(self, obj, event):
        if obj is self._host and event.type() == QEvent.Resize:
            self._reposition()
        return super().eventFilter(obj, event)