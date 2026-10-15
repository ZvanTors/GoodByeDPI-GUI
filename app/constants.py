"""Application-wide constants."""
from typing import List, NamedTuple

APP_NAME = "GoodByeDPI GUI"
APP_VERSION = "1.4.0"

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
WIKI_URL = f"{GITHUB_URL}/wiki"
LANDING_URL = f"https://{GITHUB_OWNER.lower()}.github.io/{GITHUB_REPO}/"
DONATE_PAGE_URL = f"{LANDING_URL}donate.html"

# ---------------------------------------------------------------------
# Donation
#
# Mirrors docs/donate.html — every entry shown in the dialog corresponds
# to a card on the landing page. Keep the two lists in sync whenever
# a new wallet is added.
#
# Each entry:
#   symbol   – short ticker shown in the dialog ("TRX", "USDT", …)
#   network  – blockchain / token standard ("TRC-20", "BEP-20", …)
#   address  – receive address
#   color    – brand color for the accent dot
# ---------------------------------------------------------------------
DONATION_WALLETS: List[dict] = [
    {
        "symbol":  "TRX",
        "network": "TRC-20",
        "address": "TWukNBmxLUbPVgayRsZ72u84K8yW7K9cQw",
        "color":   "#FF060A",
    },
    {
        "symbol":  "USDT",
        "network": "TRC-20",
        "address": "TWukNBmxLUbPVgayRsZ72u84K8yW7K9cQw",
        "color":   "#26A17B",
    },
    {
        "symbol":  "USDT",
        "network": "BEP-20",
        "address": "0x53f03070E2b6157fCaF48688b3426fA131c8175B",
        "color":   "#26A17B",
    },
    {
        "symbol":  "BTC",
        "network": "Native SegWit",
        "address": "bc1qt97afeun93602wuk34duj4rpxag8dt5nws4p4z",
        "color":   "#F7931A",
    },
    {
        "symbol":  "ETH",
        "network": "ERC-20",
        "address": "0x53f03070E2b6157fCaF48688b3426fA131c8175B",
        "color":   "#627EEA",
    },
    {
        "symbol":  "BNB",
        "network": "BEP-20",
        "address": "0x53f03070E2b6157fCaF48688b3426fA131c8175B",
        "color":   "#F0B90B",
    },
]

# ---------------------------------------------------------------------
# Bundled resource paths (relative — resolved via utils.resource_path)
# ---------------------------------------------------------------------
DPI_EXE_REL  = "bin/goodbyedpi.exe"
LOGO_ICO_REL = "assets/logo.ico"


# ---------------------------------------------------------------------
# Mode presets (rendered as cards on the main window)
# ---------------------------------------------------------------------
class ModePreset(NamedTuple):
    key:         str
    title:       str
    badge:       str
    icon:        str
    description: str
    args:        List[str]
    tooltip:     str


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


CUSTOM_MODE_INDEX = next(
    (i for i, m in enumerate(MODE_PRESETS) if m.key == "custom"),
    len(MODE_PRESETS) - 1,
)


def download_url(version: str) -> str:
    """Build the direct download URL for a specific release tag.

    Raises ValueError on empty input so callers never build a broken URL.
    """
    version = (version or "").strip()
    if not version:
        raise ValueError("version must be a non-empty string")
    tag = version if version.startswith(("V", "v")) else f"V{version}"
    return f"{RELEASES_PAGE}/download/{tag}/{ASSET_NAME}"