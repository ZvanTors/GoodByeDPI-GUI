"""Application-wide logging configuration.

Sets up a rotating file handler so post-crash diagnostics are possible
even when the in-app log view is gone.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from app.constants import ORG_NAME

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_MAX_BYTES = 1 * 1024 * 1024   # 1 MB per file
_BACKUP_COUNT = 3              # 4 files total

_configured = False


def _log_dir() -> str:
    """Return the directory where log files are stored.

    Uses %APPDATA% on Windows; falls back to the user home otherwise.
    """
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, ORG_NAME, "logs")
    os.makedirs(path, exist_ok=True)
    return path


def get_log_file_path() -> str:
    """Public accessor — used by the About dialog and crash dialogs."""
    return os.path.join(_log_dir(), f"{ORG_NAME}.log")


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger once.

    Safe to call multiple times — subsequent calls are no-ops. Logging
    failures never crash the application; they degrade to stderr.
    """
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    try:
        file_handler = RotatingFileHandler(
            get_log_file_path(),
            maxBytes=_MAX_BYTES,
            backupCount=_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    except OSError as exc:
        # Never crash the app over logging.
        print(f"[logging] cannot create file handler: {exc}", file=sys.stderr)

    # Mirror to stderr for developers running from source.
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    _configured = True