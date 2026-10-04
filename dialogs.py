"""Custom dialogs used by the application."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget,
)

from utils import resource_path


# ----------------------------------------------------------------
# Reusable styled card for showing a version
# ----------------------------------------------------------------
class _VersionCard(QFrame):
    def __init__(self, title: str, version: str, accent: bool = False):
        super().__init__()
        self.setObjectName("versionCard")
        self.setAttribute(Qt.WA_StyledBackground, True)

        accent_color = "#a6e3a1" if accent else "#89b4fa"
        bg = "rgba(166, 227, 161, 0.10)" if accent else "rgba(137, 180, 250, 0.08)"
        border = "rgba(166, 227, 161, 0.35)" if accent else "rgba(137, 180, 250, 0.30)"

        self.setStyleSheet(f"""
            QFrame#versionCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QLabel#cardTitle {{
                color: #a6adc8;
                font-size: 9pt;
                font-weight: 600;
                letter-spacing: 0.5px;
            }}
            QLabel#cardValue {{
                color: {accent_color};
                font-size: 20pt;
                font-weight: 800;
                letter-spacing: -0.5px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(2)

        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("cardTitle")
        title_lbl.setAlignment(Qt.AlignCenter)

        value_lbl = QLabel(version)
        value_lbl.setObjectName("cardValue")
        value_lbl.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_lbl)
        layout.addWidget(value_lbl)


# ----------------------------------------------------------------
# Modern update dialog
# ----------------------------------------------------------------
class UpdateDialog(QDialog):
    """
    A sleek, custom update dialog.

    Usage:
        dlg = UpdateDialog(parent, current="1.1.0", latest="1.2.0")
        if dlg.exec() == QDialog.Accepted:
            # user clicked Download
            ...
    """

    def __init__(self, parent, current: str, latest: str):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setModal(True)
        self.setFixedWidth(460)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            QLabel#headerTitle {
                color: #f5f5f5;
                font-size: 15pt;
                font-weight: 800;
                letter-spacing: -0.3px;
            }
            QLabel#headerBody {
                color: #a6adc8;
                font-size: 10pt;
            }
            QPushButton#laterBtn {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 9px;
                padding: 11px 22px;
                color: #cdd6f4;
                font-weight: 600;
                min-width: 90px;
            }
            QPushButton#laterBtn:hover { background-color: #45475a; }
            QPushButton#dlBtn {
                background-color: #89b4fa;
                border: none;
                border-radius: 9px;
                padding: 11px 22px;
                color: #11111b;
                font-weight: 700;
                min-width: 110px;
            }
            QPushButton#dlBtn:hover  { background-color: #a5c8ff; }
            QPushButton#dlBtn:pressed { background-color: #74a0e0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 26, 28, 24)
        root.setSpacing(20)

        # ---- Header (icon + title) ----
        header_row = QHBoxLayout()
        header_row.setSpacing(14)

        icon_label = QLabel("🎉")
        icon_label.setStyleSheet("font-size: 32pt;")
        icon_label.setFixedWidth(50)
        icon_label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        header_row.addWidget(icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(4)

        title = QLabel("Update Available")
        title.setObjectName("headerTitle")

        body = QLabel(
            "A new version of GoodByeDPI GUI is ready.<br>"
            "Download it now to get the latest improvements."
        )
        body.setObjectName("headerBody")
        body.setTextFormat(Qt.RichText)
        body.setWordWrap(True)

        text_col.addWidget(title)
        text_col.addWidget(body)
        header_row.addLayout(text_col, 1)

        root.addLayout(header_row)

        # ---- Version comparison ----
        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)

        current_card = _VersionCard("Current", f"v{current}")
        latest_card = _VersionCard("Latest", f"v{latest}", accent=True)

        arrow = QLabel("→")
        arrow.setStyleSheet("font-size: 20pt; color: #6c7086;")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setFixedWidth(30)

        cards_row.addWidget(current_card, 1)
        cards_row.addWidget(arrow)
        cards_row.addWidget(latest_card, 1)

        root.addLayout(cards_row)

        # ---- Buttons ----
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self._later_btn = QPushButton("Later")
        self._later_btn.setObjectName("laterBtn")
        self._later_btn.clicked.connect(self.reject)

        self._dl_btn = QPushButton("⬇  Download")
        self._dl_btn.setObjectName("dlBtn")
        self._dl_btn.setDefault(True)
        self._dl_btn.clicked.connect(self.accept)

        btn_row.addWidget(self._later_btn)
        btn_row.addWidget(self._dl_btn)

        root.addLayout(btn_row)