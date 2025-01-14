import os

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
    try:
        # Open the key for the current user's shell folders
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )

        # Retrieve the path to the personal (Documents) folder
        documents_path = winreg.QueryValueEx(key, "Personal")[0]

        winreg.CloseKey(key)
        return documents_path
    except Exception:
        # Fallback to a default path if retrieval fails
        pass
    return os.path.join(os.path.expanduser("~"), "Documents")


# Default paths
DEFAULT_EASE_PATH = r"C:\Program Files (x86)\AFMG\EASE GLLViewer\EASE GLLViewer.exe"
DEFAULT_GLL_PATH = r"Z:\GLL"


def create_default_settings() -> QSettings:
    settings = QSettings("spinorama.org", "GLL2TXT")

    settings.value("ease_binary_path", DEFAULT_EASE_PATH)
    settings.value("gll_files_directory", DEFAULT_GLL_PATH)
    settings.value(
        "output_directory",
        os.path.join(
            get_windows_documents_path(),
            "GLL2TXT_Output",
        ),
    )
    return settings


def validate_settings(settings: QSettings) -> tuple[list[str], list[str]]:
    """Validate that all required settings are present and valid."""
    oks = []
    errors = []

    ease_binary_path = settings.value("ease_binary_path")
    if not ease_binary_path:
        errors.append("Ease binary path is not set! Go to Settings!")
    elif not os.path.exists(ease_binary_path):
        errors.append(f"Ease binary not found: {ease_binary_path}")
    else:
        oks.append(f"Ease Binary Found! ({ease_binary_path})")

    gll_files_directory = settings.value("gll_files_directory")
    if not gll_files_directory:
        errors.append("GLL files directory is not set! Go to Settings!")
    elif not os.path.isdir(gll_files_directory):
        errors.append(f"Invalid GLL files directory: {gll_files_directory}")
    else:
        oks.append(f"Will look for GLL files in ({gll_files_directory})")

    output_directory = settings.value("output_directory")
    if not output_directory:
        errors.append("Output directory is not set! Got to Settings!")
    else:
        oks.append(f"Will generate output in ({settings.value('output_directory')})")
        os.makedirs(settings.value("output_directory"), exist_ok=True)

    return oks, errors
