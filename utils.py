"""Helper utilities used across modules."""
import ctypes
import os
import sys


def resource_path(relative_path: str) -> str:
    """Return the absolute path to a bundled resource.

    Works both when running from source and when frozen by PyInstaller.
    """
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def executable_path() -> str:
    """Return the path used to relaunch this app (EXE or script)."""
    return sys.executable if getattr(sys, "frozen", False) else sys.argv[0]


def parse_version(v: str):
    """Parse '1.2.3' into (1, 2, 3). Return None on failure."""
    try:
        return tuple(int(p) for p in v.split("."))
    except Exception:
        return None


def is_newer_version(current: str, remote: str) -> bool:
    """Return True if remote > current."""
    cur = parse_version(current)
    rem = parse_version(remote)
    if cur is None or rem is None:
        return False
    return rem > cur