"""Custom dialogs used by the application."""
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QWidget, QTabWidget, QScrollArea, QLineEdit,
)

from constants import (
    AUTHOR_NAME,
    AUTHOR_BRAND,
    GITHUB_URL,
    GOODBYEDPI_URL,
    PYSIDE_URL,
    WINDIVERT_URL,
)


# =================================================================
# Custom arguments guide data
# Format: (flag, description, insert_value, badge)
# badge: "" | "recommended" | "dangerous" | "default"
# =================================================================
CUSTOM_ARGS_GUIDE = {
    "Presets": [
        ("-1", "Legacy: most compatible mode",
         "-1", ""),
        ("-2", "Legacy: better HTTPS speed",
         "-2", ""),
        ("-3", "Legacy: HTTP + HTTPS",
         "-3", ""),
        ("-4", "Legacy: best speed",
         "-4", ""),
        ("-5", "Modern: auto-TTL, stable",
         "-5", "recommended"),
        ("-6", "Modern: fake SEQ, fast",
         "-6", "recommended"),
        ("-7", "Modern: fake checksum",
         "-7", ""),
        ("-8", "Modern: fake SEQ + checksum",
         "-8", ""),
        ("-9", "Modern: default in GoodbyeDPI",
         "-9", "default"),
    ],
    "Basic": [
        ("-p", "Block passive DPI",                     "-p",  ""),
        ("-q", "Block QUIC / HTTP3",                    "-q",  ""),
        ("-r", "Replace Host with hoSt",                "-r",  ""),
        ("-s", "Remove space after Host header",        "-s",  ""),
        ("-m", "Mix Host header case",                  "-m",  ""),
        ("-w", "Find HTTP on all processed ports",      "-w",  ""),
        ("--max-payload", "Skip payloads > 1200 bytes",
         "--max-payload", "recommended"),
    ],
    "Fragmentation": [
        ("-f <n>", "HTTP fragmentation value",
         "-f 2", ""),
        ("-k <n>", "HTTP keep-alive fragmentation",
         "-k 2", ""),
        ("-n", "Don't wait for first ACK (needs -k)",
         "-n", ""),
        ("-e <n>", "HTTPS fragmentation value",
         "-e 40", ""),
        ("--native-frag", "Split packets, don't shrink window",
         "--native-frag", "recommended"),
        ("--reverse-frag", "Send fragments in reverse order",
         "--reverse-frag", "recommended"),
        ("--frag-by-sni", "Fragment right before SNI value",
         "--frag-by-sni", ""),
    ],
    "Fake Request": [
        ("--wrong-seq", "Fake packet with past SEQ/ACK",
         "--wrong-seq", "recommended"),
        ("--wrong-chksum", "Fake packet with bad TCP checksum",
         "--wrong-chksum", ""),
        ("--set-ttl <n>", "Fake request with fixed TTL",
         "--set-ttl 5", "dangerous"),
        ("--auto-ttl", "Auto-detect TTL (safer than set-ttl)",
         "--auto-ttl", "dangerous"),
        ("--min-ttl <n>", "Min TTL distance for fake request",
         "--min-ttl 3", ""),
        ("--fake-gen <n>", "N random fake packets (max 30)",
         "--fake-gen 5", ""),
        ("--fake-resend <n>", "Send each fake packet N times",
         "--fake-resend 2", ""),
        ("--fake-with-sni <d>", "Fake Firefox TLS with given SNI",
         "--fake-with-sni example.com", ""),
    ],
    "Advanced": [
        ("--port <n>", "Fragment additional TCP port",
         "--port 443", ""),
        ("--ip-id <n>", "Handle additional IP ID",
         "--ip-id 1234", ""),
        ("--blacklist <f>", "Apply tricks only to hosts in file",
         "--blacklist blacklist.txt", ""),
        ("--allow-no-sni", "Apply tricks even if SNI not detected",
         "--allow-no-sni", ""),
        ("--dns-addr <ip>", "Redirect UDP DNS to IP",
         "--dns-addr 1.1.1.1", ""),
        ("--dns-port <n>", "Redirect UDP DNS to port",
         "--dns-port 53", ""),
        ("--dnsv6-addr <ip>", "Redirect UDPv6 DNS to IPv6",
         "--dnsv6-addr ::1", ""),
        ("--dnsv6-port <n>", "Redirect UDPv6 DNS to port",
         "--dnsv6-port 53", ""),
        ("--dns-verb", "Verbose DNS redirection logs",
         "--dns-verb", ""),
    ],
}

_BADGE_STYLE = {
    "recommended": (
        "background-color: rgba(166, 227, 161, 0.12);"
        "color: #a6e3a1;"
        "border: 1px solid rgba(166, 227, 161, 0.35);"
    ),
    "dangerous": (
        "background-color: rgba(249, 226, 175, 0.12);"
        "color: #f9e2af;"
        "border: 1px solid rgba(249, 226, 175, 0.35);"
    ),
    "default": (
        "background-color: rgba(137, 180, 250, 0.12);"
        "color: #89b4fa;"
        "border: 1px solid rgba(137, 180, 250, 0.35);"
    ),
}


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
                color: #a6adc8; font-size: 9pt;
                font-weight: 600; letter-spacing: 0.5px;
            }}
            QLabel#cardValue {{
                color: {accent_color}; font-size: 20pt;
                font-weight: 800; letter-spacing: -0.5px;
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
# Update dialog
# ----------------------------------------------------------------
class UpdateDialog(QDialog):
    def __init__(self, parent, current: str, latest: str):
        super().__init__(parent)
        self.setWindowTitle("Update Available")
        self.setModal(True)
        self.setFixedWidth(460)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            QLabel#headerTitle {
                color: #f5f5f5; font-size: 15pt;
                font-weight: 800; letter-spacing: -0.3px;
            }
            QLabel#headerBody { color: #a6adc8; font-size: 10pt; }
            QPushButton#laterBtn {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 9px; padding: 11px 22px;
                color: #cdd6f4; font-weight: 600; min-width: 90px;
            }
            QPushButton#laterBtn:hover { background-color: #45475a; }
            QPushButton#dlBtn {
                background-color: #89b4fa; border: none; border-radius: 9px;
                padding: 11px 22px; color: #11111b;
                font-weight: 700; min-width: 110px;
            }
            QPushButton#dlBtn:hover   { background-color: #a5c8ff; }
            QPushButton#dlBtn:pressed { background-color: #74a0e0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 26, 28, 24)
        root.setSpacing(20)

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


# ----------------------------------------------------------------
# About dialog
# ----------------------------------------------------------------
class AboutDialog(QDialog):
    def __init__(self, parent, version: str):
        super().__init__(parent)
        self.setWindowTitle("About GoodByeDPI GUI")
        self.setModal(True)
        self.setFixedWidth(480)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            QLabel#aboutTitle {
                color: #f5f5f5; font-size: 16pt;
                font-weight: 800; letter-spacing: -0.3px;
            }
            QLabel#aboutSubtitle { color: #a6adc8; font-size: 9.5pt; }
            QLabel#aboutVersion {
                background-color: rgba(166, 227, 161, 0.12);
                color: #a6e3a1; border: 1px solid rgba(166, 227, 161, 0.35);
                border-radius: 12px; padding: 4px 14px;
                font-size: 9pt; font-weight: 700; letter-spacing: 0.3px;
            }
            QFrame#aboutSection {
                background-color: #1e1e2e; border: 1px solid #313244;
                border-radius: 12px;
            }
            QLabel#aboutSectionTitle {
                color: #6c7086; font-size: 8.5pt;
                font-weight: 700; letter-spacing: 1.2px;
            }
            QLabel#aboutItemDot  { color: #89b4fa; font-size: 8pt; }
            QLabel#aboutItemName { font-size: 10pt; color: #cdd6f4; }
            QLabel#aboutItemDesc { color: #6c7086; font-size: 9pt; }
            QFrame#aboutCredit {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(137, 180, 250, 0.08),
                    stop:1 rgba(166, 227, 161, 0.08)
                );
                border: 1px solid rgba(137, 180, 250, 0.20);
                border-radius: 12px;
            }
            QLabel#aboutHeart  { color: #f38ba8; font-size: 11pt; }
            QLabel#aboutMuted  { color: #6c7086; font-size: 9pt; }
            QLabel#aboutAuthor { color: #89b4fa; font-size: 9pt; font-weight: 700; }
            QLabel#aboutBrand  { color: #a6e3a1; font-size: 9pt; font-weight: 700; }
            QPushButton#aboutGithubBtn {
                background-color: #313244; border: 1px solid #45475a;
                border-radius: 9px; padding: 10px 20px;
                color: #cdd6f4; font-weight: 600; min-width: 100px;
            }
            QPushButton#aboutGithubBtn:hover   { background-color: #45475a; border-color: #585b70; }
            QPushButton#aboutGithubBtn:pressed { background-color: #585b70; }
            QPushButton#aboutCloseBtn {
                background-color: #89b4fa; border: none; border-radius: 9px;
                padding: 10px 22px; color: #11111b;
                font-weight: 700; min-width: 100px;
            }
            QPushButton#aboutCloseBtn:hover   { background-color: #a5c8ff; }
            QPushButton#aboutCloseBtn:pressed { background-color: #74a0e0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 26, 28, 24)
        root.setSpacing(16)
        root.addLayout(self._build_header(version))
        root.addWidget(self._build_powered_by())
        root.addWidget(self._build_credit())
        root.addLayout(self._build_buttons())

    def _build_header(self, version: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)
        icon = QLabel("🛡")
        icon.setStyleSheet("font-size: 36pt;")
        icon.setFixedWidth(56)
        icon.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        row.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title = QLabel("GoodByeDPI GUI")
        title.setObjectName("aboutTitle")
        subtitle = QLabel("Bypass Deep Packet Inspection on Windows")
        subtitle.setObjectName("aboutSubtitle")
        subtitle.setWordWrap(True)
        text_col.addWidget(title)
        text_col.addWidget(subtitle)
        row.addLayout(text_col, 1)

        badge = QLabel(f"v{version}")
        badge.setObjectName("aboutVersion")
        row.addWidget(badge, 0, Qt.AlignTop)
        return row

    def _build_powered_by(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("aboutSection")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(10)

        title = QLabel("POWERED BY")
        title.setObjectName("aboutSectionTitle")
        layout.addWidget(title)

        items = [
            ("GoodbyeDPI", "Core engine",    GOODBYEDPI_URL),
            ("PySide6",    "GUI framework",  PYSIDE_URL),
            ("WinDivert",  "Packet capture", WINDIVERT_URL),
        ]
        for name, desc, url in items:
            layout.addLayout(self._build_item_row(name, desc, url))
        return frame

    def _build_item_row(self, name: str, desc: str, url: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        dot = QLabel("●")
        dot.setObjectName("aboutItemDot")
        dot.setFixedWidth(10)

        name_lbl = QLabel(
            f'<a href="{url}" style="color:#89b4fa; text-decoration:none;">'
            f'<b>{name}</b></a>'
        )
        name_lbl.setObjectName("aboutItemName")
        name_lbl.setTextFormat(Qt.RichText)
        name_lbl.setOpenExternalLinks(True)
        name_lbl.setCursor(Qt.PointingHandCursor)

        desc_lbl = QLabel(desc)
        desc_lbl.setObjectName("aboutItemDesc")

        row.addWidget(dot)
        row.addWidget(name_lbl)
        row.addStretch()
        row.addWidget(desc_lbl)
        return row

    def _build_credit(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("aboutCredit")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(7)

        heart = QLabel("❤");       heart.setObjectName("aboutHeart")
        made = QLabel("Made with"); made.setObjectName("aboutMuted")
        auth = QLabel(AUTHOR_NAME); auth.setObjectName("aboutAuthor")
        dot  = QLabel("·");         dot.setObjectName("aboutMuted")
        brand= QLabel(AUTHOR_BRAND);brand.setObjectName("aboutBrand")

        for w in (heart, made, auth, dot, brand):
            layout.addWidget(w)
        layout.addStretch()
        return frame

    def _build_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        github_btn = QPushButton("⭐  GitHub")
        github_btn.setObjectName("aboutGithubBtn")
        github_btn.setCursor(Qt.PointingHandCursor)
        github_btn.clicked.connect(self._open_github)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("aboutCloseBtn")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)

        row.addWidget(github_btn)
        row.addStretch()
        row.addWidget(close_btn)
        return row

    def _open_github(self) -> None:
        QDesktopServices.openUrl(QUrl(GITHUB_URL))


# ----------------------------------------------------------------
# Custom Arguments Help dialog
# ----------------------------------------------------------------
class CustomArgsHelpDialog(QDialog):
    """A tabbed guide to GoodbyeDPI command-line arguments.

    Usage:
        dlg = CustomArgsHelpDialog(parent, current_args="-f 2")
        if dlg.exec() == QDialog.Accepted:
            new_args = dlg.result_args()
    """

    def __init__(self, parent, current_args: str = ""):
        super().__init__(parent)
        self.setWindowTitle("GoodbyeDPI Arguments Guide")
        self.setModal(True)
        self.resize(680, 640)
        self.setMinimumSize(560, 520)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

        self._all_items: list[QFrame] = []

        self.setStyleSheet("""
            QDialog { background-color: #11111b; }
            QLabel { color: #cdd6f4; background: transparent; }

            QLabel#guideTitle {
                color: #f5f5f5; font-size: 15pt;
                font-weight: 800; letter-spacing: -0.3px;
            }
            QLabel#guideHint {
                color: #6c7086; font-size: 9pt;
            }

            QLineEdit#argSearch {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 8px 14px;
                color: #cdd6f4;
                font-size: 9.5pt;
            }
            QLineEdit#argSearch:focus { border-color: #89b4fa; }

            /* Tabs */
            QTabWidget::pane {
                border: none; background: transparent; top: -1px;
            }
            QTabBar { background: transparent; }
            QTabBar::tab {
                background-color: #1e1e2e;
                color: #a6adc8;
                border: 1px solid #313244;
                border-radius: 8px;
                padding: 7px 14px;
                margin-right: 5px;
                font-weight: 600;
                font-size: 9pt;
            }
            QTabBar::tab:selected {
                background-color: #89b4fa;
                color: #11111b;
                border-color: #89b4fa;
            }
            QTabBar::tab:hover:!selected {
                background-color: #313244;
                color: #cdd6f4;
            }

            /* Item cards */
            QFrame#argItem {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 10px;
            }
            QFrame#argItem:hover { border-color: #45475a; }

            QLabel#argFlag {
                font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
                color: #89b4fa;
                font-size: 10pt;
                font-weight: 700;
            }
            QLabel#argDesc {
                color: #cdd6f4;
                font-size: 9.5pt;
            }
            QLabel#argBadge {
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 7.5pt;
                font-weight: 800;
                letter-spacing: 0.6px;
            }

            QPushButton#argAddBtn {
                background-color: rgba(166, 227, 161, 0.10);
                color: #a6e3a1;
                border: 1px solid rgba(166, 227, 161, 0.30);
                border-radius: 9px;
                font-weight: 800;
                font-size: 14pt;
                padding: 0;
                min-width: 0;   max-width: 34px;
                min-height: 0;  max-height: 34px;
            }
            QPushButton#argAddBtn:hover {
                background-color: rgba(166, 227, 161, 0.22);
                border-color: rgba(166, 227, 161, 0.55);
            }
            QPushButton#argAddBtn:pressed {
                background-color: rgba(166, 227, 161, 0.32);
            }

            QLabel#argPreviewLabel {
                color: #6c7086;
                font-size: 8.5pt;
                font-weight: 700;
                letter-spacing: 0.8px;
            }
            QLineEdit#argPreview {
                background-color: #0d0d15;
                border: 1px solid #262637;
                border-radius: 8px;
                padding: 9px 12px;
                color: #a6e3a1;
                font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
                font-size: 9.5pt;
            }

            QPushButton#argClearBtn {
                background-color: transparent;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px 18px;
                color: #a6adc8;
                font-weight: 600;
                min-width: 80px; min-height: 0;
            }
            QPushButton#argClearBtn:hover {
                background-color: #313244; color: #cdd6f4;
            }
            QPushButton#argApplyBtn {
                background-color: #89b4fa;
                border: none;
                border-radius: 8px;
                padding: 8px 22px;
                color: #11111b;
                font-weight: 700;
                min-width: 100px; min-height: 0;
            }
            QPushButton#argApplyBtn:hover   { background-color: #a5c8ff; }
            QPushButton#argApplyBtn:pressed { background-color: #74a0e0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 20)
        root.setSpacing(14)

        root.addLayout(self._build_header())

        # ---- Search box ----
        self._search = QLineEdit()
        self._search.setObjectName("argSearch")
        self._search.setPlaceholderText(
            "🔍  Search arguments…  (e.g.  frag,  ttl,  sni)"
        )
        self._search.textChanged.connect(self._on_search)
        root.addWidget(self._search)

        # ---- Tabs ----
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        for category, items in CUSTOM_ARGS_GUIDE.items():
            is_preset = (category == "Presets")
            self._tabs.addTab(
                self._build_category_tab(items, replace=is_preset),
                category,
            )
        root.addWidget(self._tabs, 1)

        # ---- Live preview ----
        preview_box = QVBoxLayout()
        preview_box.setSpacing(4)

        preview_label = QLabel("CURRENT ARGUMENTS")
        preview_label.setObjectName("argPreviewLabel")

        self._preview = QLineEdit()
        self._preview.setObjectName("argPreview")
        self._preview.setReadOnly(True)
        self._preview.setText(current_args.strip())

        preview_box.addWidget(preview_label)
        preview_box.addWidget(self._preview)
        root.addLayout(preview_box)

        # ---- Buttons ----
        root.addLayout(self._build_footer())

    # ----------------------------------------------------------------
    def _build_header(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(14)

        icon = QLabel("📖")
        icon.setStyleSheet("font-size: 32pt; background: transparent;")
        icon.setFixedWidth(50)
        icon.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        row.addWidget(icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)

        title = QLabel("Arguments Guide")
        title.setObjectName("guideTitle")

        hint = QLabel(
            "Click  <span style='color:#a6e3a1; font-weight:700;'>+</span>  "
            "to append a flag.  In the "
            "<span style='color:#89b4fa; font-weight:700;'>Presets</span> "
            "tab,  <b>+</b>  replaces the whole line."
        )
        hint.setObjectName("guideHint")
        hint.setTextFormat(Qt.RichText)
        hint.setWordWrap(True)

        text_col.addWidget(title)
        text_col.addWidget(hint)
        row.addLayout(text_col, 1)
        return row

    # ----------------------------------------------------------------
    def _build_category_tab(self, items: list, replace: bool) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 10, 6, 10)
        layout.setSpacing(8)

        for flag, desc, insert, badge in items:
            item = self._build_item(flag, desc, insert, badge, replace)
            self._all_items.append(item)
            layout.addWidget(item)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    # ----------------------------------------------------------------
    def _build_item(self, flag: str, desc: str, insert: str,
                    badge: str, replace: bool) -> QFrame:
        frame = QFrame()
        frame.setObjectName("argItem")
        frame.setAttribute(Qt.WA_StyledBackground, True)
        frame.setProperty("search", f"{flag} {desc} {insert}".lower())

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 12, 10)
        layout.setSpacing(12)

        flag_lbl = QLabel(flag)
        flag_lbl.setObjectName("argFlag")
        flag_lbl.setMinimumWidth(150)
        flag_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(flag_lbl)

        if badge and badge in _BADGE_STYLE:
            badge_lbl = QLabel(badge.upper())
            badge_lbl.setObjectName("argBadge")
            badge_lbl.setStyleSheet(_BADGE_STYLE[badge])
            layout.addWidget(badge_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setObjectName("argDesc")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl, 1)

        add_btn = QPushButton("+")
        add_btn.setObjectName("argAddBtn")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setFixedSize(34, 34)
        add_btn.setToolTip(
            "Replace arguments with this preset" if replace
            else f"Append:  {insert}"
        )
        add_btn.clicked.connect(
            lambda _=False, v=insert, r=replace: self._apply(v, r)
        )
        layout.addWidget(add_btn, 0, Qt.AlignVCenter)

        return frame

    # ----------------------------------------------------------------
    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)

        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("argClearBtn")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("argClearBtn")
        cancel_btn.setCursor(Qt.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        apply_btn = QPushButton("Apply")
        apply_btn.setObjectName("argApplyBtn")
        apply_btn.setCursor(Qt.PointingHandCursor)
        apply_btn.setDefault(True)
        apply_btn.clicked.connect(self.accept)

        row.addWidget(clear_btn)
        row.addStretch()
        row.addWidget(cancel_btn)
        row.addWidget(apply_btn)
        return row

    # ----------------------------------------------------------------
    def _apply(self, value: str, replace: bool) -> None:
        if replace:
            self._preview.setText(value)
            return
        current = self._preview.text().strip()
        self._preview.setText(f"{current} {value}".strip() if current else value)

    def _clear(self) -> None:
        self._preview.clear()

    def _on_search(self, text: str) -> None:
        needle = text.lower().strip()
        for item in self._all_items:
            haystack = item.property("search") or ""
            item.setVisible(not needle or needle in haystack)

    # ----------------------------------------------------------------
    def result_args(self) -> str:
        return self._preview.text().strip()