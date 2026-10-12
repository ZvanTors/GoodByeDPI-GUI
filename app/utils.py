"""Helper utilities used across modules."""
import ctypes
import logging
import os
import sys

log = logging.getLogger(__name__)


def resource_path(relative_path: str) -> str:
    """Return the absolute path to a bundled resource.

    - Frozen:  resources live next to the EXE inside ``sys._MEIPASS``.
    - Source:  the project root (parent of the ``app/`` package) is used.
    """
    if getattr(sys, "frozen", False):
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError) as exc:
        log.debug("is_admin check failed: %s", exc)
        return False


def executable_path() -> str:
    """Return the path used to relaunch this app (EXE or script)."""
    if getattr(sys, "frozen", False):
        return sys.executable
    argv0 = (sys.argv[0] if sys.argv else "").strip()
    if not argv0:
        # Extremely rare, but some IDEs give an empty argv[0].
        return os.path.abspath("main.py")
    return os.path.abspath(argv0)


def parse_version(v: str):
    """Parse '1.2.3' into (1, 2, 3). Return None on failure.

    Pre-release suffixes ('1.2.3-beta') are stripped before parsing.
    """
    if not v:
        return None
    try:
        head = v.strip().lstrip("vV").split("-", 1)[0].split("+", 1)[0]
        return tuple(int(p) for p in head.split("."))
    except (ValueError, AttributeError) as exc:
        log.debug("parse_version failed for %r: %s", v, exc)
        return None


def is_newer_version(current: str, remote: str) -> bool:
    """Return True if remote > current."""
    cur = parse_version(current)
    rem = parse_version(remote)
    if cur is None or rem is None:
        return False
    return rem > cur