"""Modern dark theme (QSS)."""

DARK_QSS = """
/* ================================================================
   Base
================================================================ */
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #11111b, stop:1 #181825
    );
}

QWidget {
    background-color: #11111b;
    color: #cdd6f4;
    font-family: 'Segoe UI Variable', 'Segoe UI', 'Inter', sans-serif;
    font-size: 10pt;
}

/* Central widget must be transparent so the window gradient shows
   through. Without this, the base QWidget rule paints a solid color. */
QWidget#centralWidget {
    background: transparent;
}

/* Transparent container for the custom-arguments row
   (prevents the black rectangle from showing inside the group box) */
QWidget#customArgsContainer {
    background: transparent;
}

/* ================================================================
   Group boxes – floating pill title
================================================================ */
QGroupBox {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 14px;
    margin-top: 18px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 18px;
    top: 2px;
    padding: 5px 14px;
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 10px;
    color: #89b4fa;
    font-size: 9.5pt;
    font-weight: 700;
    letter-spacing: 0.4px;
}

/* ================================================================
   Header frame
================================================================ */
QFrame#headerFrame {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #1e1e2e, stop:1 #181825
    );
    border: 1px solid #313244;
    border-radius: 14px;
}

/* ================================================================
   Labels
================================================================ */
QLabel { background: transparent; color: #cdd6f4; }

QLabel#appTitle {
    font-size: 16pt;
    font-weight: 800;
    color: #f5f5f5;
    letter-spacing: -0.3px;
}
QLabel#appSubtitle {
    color: #7f849c;
    font-size: 9pt;
}
QLabel#fieldLabel {
    color: #a6adc8;
    font-size: 9.5pt;
    font-weight: 500;
}

/* ================================================================
   Version badge (clickable button in header)
================================================================ */
QPushButton#versionBadge {
    background-color: rgba(166, 227, 161, 0.12);
    color: #a6e3a1;
    border: 1px solid rgba(166, 227, 161, 0.35);
    border-radius: 12px;
    padding: 4px 14px;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.3px;
    min-width: 0;
    min-height: 0;
}
QPushButton#versionBadge:hover {
    background-color: rgba(166, 227, 161, 0.22);
    border-color: rgba(166, 227, 161, 0.55);
}
QPushButton#versionBadge:pressed {
    background-color: rgba(166, 227, 161, 0.32);
}

/* ================================================================
   Help button (?) next to Custom arguments
================================================================ */
QPushButton#helpBtn {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 18px;
    color: #89b4fa;
    font-size: 12pt;
    font-weight: 800;
    padding: 0;
    min-width: 0;   max-width: 40px;
    min-height: 0;  max-height: 36px;
}
QPushButton#helpBtn:hover {
    background-color: #45475a;
    border-color: #89b4fa;
    color: #a5c8ff;
}
QPushButton#helpBtn:pressed {
    background-color: #585b70;
}

/* ================================================================
   Credit badge
================================================================ */
QFrame#creditBadge {
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(137, 180, 250, 0.08),
        stop:1 rgba(166, 227, 161, 0.08)
    );
    border: 1px solid rgba(137, 180, 250, 0.20);
    border-radius: 14px;
}
QLabel#creditHeart   { color: #f38ba8; font-size: 11pt; }
QLabel#creditBy      { color: #6c7086; font-size: 8.5pt; }
QLabel#creditAuthor  { color: #89b4fa; font-size: 8.5pt;
                       font-weight: 700; letter-spacing: 0.3px; }
QLabel#creditBrand   { color: #a6e3a1; font-size: 8.5pt;
                       font-weight: 700; letter-spacing: 0.3px; }

/* ================================================================
   Inputs
================================================================ */
QComboBox, QLineEdit {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 9px;
    padding: 9px 14px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
    min-height: 18px;
}
QComboBox:hover, QLineEdit:hover { border: 1px solid #585b70; }
QComboBox:focus, QLineEdit:focus { border: 1px solid #89b4fa; }

QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #cdd6f4;
    margin-right: 10px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 9px;
    padding: 5px;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    border-radius: 6px;
    min-height: 22px;
}
/* Disabled style kept as a fallback – no longer used in normal flow */
QLineEdit:disabled {
    background-color: #252537;
    color: #6c7086;
    border: 1px dashed #313244;
}

/* ================================================================
   Buttons
================================================================ */
QPushButton {
    background-color: #313244;
    border: 1px solid #45475a;
    border-radius: 9px;
    padding: 10px 22px;
    color: #cdd6f4;
    font-weight: 600;
    min-width: 100px;
    min-height: 20px;
}
QPushButton:hover   { background-color: #45475a; border-color: #585b70; }
QPushButton:pressed { background-color: #585b70; }
QPushButton:disabled {
    color: #6c7086;
    background-color: #1e1e2e;
    border-color: #313244;
}

QPushButton#startBtn {
    background-color: #a6e3a1;
    color: #11111b;
    border: none;
}
QPushButton#startBtn:hover    { background-color: #b8ecb4; }
QPushButton#startBtn:pressed  { background-color: #94e2d5; }
QPushButton#startBtn:disabled { background-color: #1e1e2e; color: #585b70; }

QPushButton#stopBtn {
    background-color: #f38ba8;
    color: #11111b;
    border: none;
}
QPushButton#stopBtn:hover    { background-color: #eba0ac; }
QPushButton#stopBtn:pressed  { background-color: #e64553; }
QPushButton#stopBtn:disabled { background-color: #1e1e2e; color: #585b70; }

QPushButton#updateBtn {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    border-radius: 10px;
    padding: 9px 18px;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 0.3px;
    min-width: 0;
    min-height: 0;
}
QPushButton#updateBtn:hover   { background-color: #a5c8ff; }
QPushButton#updateBtn:pressed { background-color: #74a0e0; }

QPushButton#smallBtn {
    min-width: 80px;
    padding: 6px 16px;
    font-size: 9pt;
}

/* ================================================================
   Output log
================================================================ */
QTextEdit {
    background-color: #0d0d15;
    border: 1px solid #262637;
    border-radius: 9px;
    padding: 12px 14px;
    color: #a6e3a1;
    font-family: 'Cascadia Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 9pt;
    selection-background-color: #89b4fa;
    selection-color: #11111b;
}

/* ================================================================
   Checkboxes – fully transparent
================================================================ */
QCheckBox {
    spacing: 10px;
    color: #cdd6f4;
    padding: 4px 0;
    background: transparent;
    border: none;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #585b70;
    background-color: #313244;
}
QCheckBox::indicator:hover { border: 1px solid #89b4fa; }
QCheckBox::indicator:checked {
    background-color: #89b4fa;
    border: 1px solid #89b4fa;
}
QCheckBox::indicator:checked:hover { background-color: #b4befe; }

/* ================================================================
   Menus
================================================================ */
QMenu {
    background-color: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 10px;
    padding: 8px;
    color: #cdd6f4;
}
QMenu::item {
    padding: 9px 28px 9px 16px;
    border-radius: 6px;
    font-size: 9.5pt;
}
QMenu::item:selected { background-color: #89b4fa; color: #11111b; }
QMenu::item:disabled { color: #6c7086; }
QMenu::separator { height: 1px; background: #313244; margin: 6px 10px; }

/* ================================================================
   Scrollbars
================================================================ */
QScrollBar:vertical {
    background: transparent; width: 10px; margin: 4px;
}
QScrollBar::handle:vertical {
    background: #45475a; border-radius: 4px; min-height: 28px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }

QScrollBar:horizontal {
    background: transparent; height: 10px; margin: 4px;
}
QScrollBar::handle:horizontal {
    background: #45475a; border-radius: 4px; min-width: 28px;
}
QScrollBar::handle:horizontal:hover { background: #585b70; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }

/* ================================================================
   Dialogs
================================================================ */
QDialog { background-color: #11111b; }
QMessageBox  { background-color: #1e1e2e; }
QMessageBox QLabel { color: #cdd6f4; font-size: 10pt; }
"""