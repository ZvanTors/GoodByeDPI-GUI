"""Reusable custom widgets (status indicators, uptime chip)."""
import time

from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QLabel, QSizePolicy,
    QGraphicsOpacityEffect,
)


# ------------------------------------------------------------------
# Animated status dot
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# Status pill (dot + text)
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# Uptime chip (⏱ 00:00:00)
# ------------------------------------------------------------------
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