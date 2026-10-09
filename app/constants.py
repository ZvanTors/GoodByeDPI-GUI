"""Application-wide constants."""

APP_NAME = "GoodByeDPI GUI"
APP_VERSION = "1.2.0"

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

# Mode presets: (label, arguments, tooltip)
MODE_PRESETS = [
    ("Fast  —  Recommended",
     ["-6"],
     "Fast & aggressive bypass (GoodbyeDPI flag: -6).\n"
     "Uses reverse fragmentation + fake SEQ.\n"
     "Works for most ISPs."),
    ("Compatible  —  Fallback",
     ["-5"],
     "Gentler bypass (GoodbyeDPI flag: -5).\n"
     "Try this if Fast mode causes issues."),
    ("Custom arguments",
     [],
     "Enter your own GoodbyeDPI command-line arguments."),
]


def download_url(version: str) -> str:
    """Build the direct download URL for a specific release tag.

    Example:
        download_url("1.2.0") ->
        https://github.com/ZvanTors/GoodByeDPI-GUI/releases/download/V1.2.0/GoodByeDPI.GUI.exe
    """
    tag = version if version.startswith(("V", "v")) else f"V{version}"
    return f"{RELEASES_PAGE}/download/{tag}/{ASSET_NAME}"