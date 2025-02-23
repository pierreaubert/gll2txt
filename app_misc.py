import os
import sys
from pathlib import Path
from typing import List, Tuple

from PySide6.QtCore import QSettings

WINDOWS = True
try:
    import winreg
except ModuleNotFoundError:
    WINDOWS = False


def get_windows_documents_path() -> str:
    """
    Retrieve the user's Documents folder path on Windows
    """
    if WINDOWS:
        try:
            # Open the key for the current user's shell folders
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            )

            # Retrieve the path to the personal (Documents) folder
            documents_path = winreg.QueryValueEx(key, "Personal")[0]

            winreg.CloseKey(key)
            return str(documents_path)
        except Exception:
            # Fallback to a default path if retrieval fails
            sys.exit("Failed to get home directory")

    return str(Path(os.path.expanduser("~")) / "Documents")


# Default paths
DEFAULT_EASE_PATH = r"C:\Program Files (x86)\AFMG\EASE GLLViewer\EASE GLLViewer.exe"


def create_default_settings() -> QSettings:
    settings = QSettings("spinorama.org", "GLL2TXT")

    # Set default values if they don't exist
    if not settings.value("ease_binary_path"):
        settings.setValue("ease_binary_path", DEFAULT_EASE_PATH)
    if not settings.value("gll_files_directory"):
        settings.setValue("gll_files_directory", get_windows_documents_path() + "/GLL")
    if not settings.value("output_directory"):
        settings.setValue("output_directory", get_windows_documents_path() + "/GLL2TXT")
    return settings


def validate_settings(settings: QSettings) -> Tuple[bool, List[str]]:
    """
    Validate settings

    Args:
        settings (QSettings): Settings to validate

    Returns:
        Tuple[bool, List[str]]: Tuple containing validation result and list of error messages
    """
    errors = []
    ease_binary = settings.value("ease_binary_path")
    gll_dir = settings.value("gll_files_directory")
    output_dir = settings.value("output_directory")

    if not ease_binary:
        errors.append("Ease binary path is not set! Go to Settings!")
    elif not os.path.exists(ease_binary):
        if WINDOWS:
            errors.append(f"Invalid Ease binary path: {ease_binary}")
        else:
            errors.append(
                "Cannot run Ease since you are not on Windows! Other parts of the application are working."
            )

    if not gll_dir:
        errors.append("GLL files directory is not set! Go to Settings!")
    elif not os.path.exists(gll_dir):
        errors.append(f"Invalid GLL files directory: {gll_dir}")

    if not output_dir:
        errors.append("Output directory is not set! Got to Settings!")
    elif not os.path.exists(output_dir):
        errors.append(f"Invalid output directory: {output_dir}")

    return len(errors) == 0, errors
