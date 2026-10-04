"""Entry point for GoodByeDPI GUI."""
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from constants import APP_NAME, ORG_NAME
from controller import AppController
from utils import is_admin


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setStyle("Fusion")  # Ensures QSS is rendered fully on Windows

    if not is_admin():
        QMessageBox.critical(
            None, "Administrator Required",
            "GoodByeDPI GUI must be run as Administrator.\n\n"
            "Right-click the app and choose 'Run as administrator'.",
        )
        return 1

    controller = AppController()
    controller.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())