"""Qt initialization module.

This module must be imported before any other Qt imports to properly set up the Qt environment.
"""

import os

os.environ["QT_API"] = "pyside6"

# These must be set before importing Qt modules
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication


def init_qt():
    """Initialize Qt application settings.
    Must be called before creating QApplication instance.
    """
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    QApplication.setAttribute(
        Qt.AA_ShareOpenGLContexts, True
    )  # Help with threading issues
