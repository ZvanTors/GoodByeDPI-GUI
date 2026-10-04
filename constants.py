"""Application-wide constants."""

APP_NAME = "GoodByeDPI GUI"
APP_VERSION = "1.2.0"

# GitHub repository info
GITHUB_OWNER = "ZvanTors"
GITHUB_REPO = "GoodByeDPI-GUI"
RELEASES_PAGE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
RELEASES_LATEST = f"{RELEASES_PAGE}/latest"

# Name of the EXE asset attached to each release.
ASSET_NAME = "GoodByeDPI.GUI.exe"

# Windows Task Scheduler entry
TASK_NAME = "GoodbyeDPIManager"

# QSettings identifiers
ORG_NAME = "GoodbyeDPIManager"
APP_KEY = "GUI"

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