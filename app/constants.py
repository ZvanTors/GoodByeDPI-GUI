"""Application-wide constants."""
from typing import List, NamedTuple

APP_NAME = "GoodByeDPI GUI"
APP_VERSION = "1.3.0"

# GitHub repository info
GITHUB_OWNER = "ZvanTors"
GITHUB_REPO = "GoodByeDPI-GUI"
GITHUB_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
RELEASES_PAGE = f"{GITHUB_URL}/releases"
RELEASES_LATEST = f"{RELEASES_PAGE}/latest"

# Name of the EXE asset attached to each release.
ASSET_NAME = "GoodByeDPI.GUI.exe"

# Windows Task Scheduler entry
TASK_NAME = "GoodbyeDPIManager"

# QSettings identifiers
ORG_NAME = "GoodbyeDPIManager"
APP_KEY = "GUI"

# Credits / About dialog
AUTHOR_NAME = "AmooReza"
AUTHOR_BRAND = "WhiteDNS"

# External resources (About dialog links)
GOODBYEDPI_URL = "https://github.com/ValdikSS/GoodbyeDPI"
PYSIDE_URL = "https://pypi.org/project/PySide6/"
WINDIVERT_URL = "https://www.reqrypt.org/windivert.html"

# ---------------------------------------------------------------------
# Bundled resource paths (relative — resolved via utils.resource_path)
# ---------------------------------------------------------------------
DPI_EXE_REL  = "bin/goodbyedpi.exe"
LOGO_ICO_REL = "assets/logo.ico"


# ---------------------------------------------------------------------
# Mode presets (rendered as cards on the main window)
# ---------------------------------------------------------------------
class ModePreset(NamedTuple):
    key:         str          # stable identifier, used for lookups
    title:       str          # short name shown on the card
    badge:       str          # small pill label ("" = none)
    icon:        str          # single emoji / glyph
    description: str          # one-line explanation under the title
    args:        List[str]    # GoodbyeDPI arguments passed at start
    tooltip:     str          # long hover text


MODE_PRESETS: List[ModePreset] = [
    ModePreset(
        key="fast",
        title="Fast",
        badge="Recommended",
        icon="⚡",
        description="Reverse fragmentation + fake SEQ",
        args=["-6"],
        tooltip=(
            "Fast & aggressive bypass (GoodbyeDPI flag: -6).\n"
            "Uses reverse fragmentation + fake SEQ.\n"
            "Works for most ISPs."
        ),
    ),
    ModePreset(
        key="compatible",
        title="Compatible",
        badge="Fallback",
        icon="🛡",
        description="Gentler fragmentation preset",
        args=["-5"],
        tooltip=(
            "Gentler bypass (GoodbyeDPI flag: -5).\n"
            "Try this if Fast mode causes issues."
        ),
    ),
    ModePreset(
        key="custom",
        title="Custom",
        badge="",
        icon="🔧",
        description="Your own GoodbyeDPI flags",
        args=[],
        tooltip="Enter your own GoodbyeDPI command-line arguments.",
    ),
]


# Convenient lookups
CUSTOM_MODE_INDEX = next(
    (i for i, m in enumerate(MODE_PRESETS) if m.key == "custom"),
    len(MODE_PRESETS) - 1,
)


def download_url(version: str) -> str:
    """Build the direct download URL for a specific release tag."""
    tag = version if version.startswith(("V", "v")) else f"V{version}"
    return f"{RELEASES_PAGE}/download/{tag}/{ASSET_NAME}"