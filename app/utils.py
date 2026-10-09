"""Helper utilities used across modules."""
import ctypes
import os
import sys


def resource_path(relative_path: str) -> str:
    """Return the absolute path to a bundled resource.

    Works both when running from source and when frozen by PyInstaller.

    - Frozen:  resources live next to the EXE inside ``sys._MEIPASS``
               (PyInstaller extracts ``--add-data`` targets there).
    - Source:  the project root (parent of the ``app/`` package) is used
               as the base, so ``bin/`` and ``assets/`` are found at the
               repository root, regardless of the current working dir.
    """
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        # app/utils.py  ->  app/  ->  project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def is_admin() -> bool:
    """Return True if the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def executable_path() -> str:
    """Return the path used to relaunch this app (EXE or script).

    In frozen mode this is the EXE itself; in source mode this is
    ``main.py`` resolved to an absolute path so that Task Scheduler
    entries work regardless of the current working directory.
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


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