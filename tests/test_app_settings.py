import pytest

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QLineEdit, QPushButton, QFileDialog

from app_settings import SettingsDialog


@pytest.fixture
def settings():
    """Create test settings"""
    settings = QSettings()
    settings.clear()
    return settings


@pytest.fixture
def dialog(qapp, settings):
    """Create SettingsDialog instance"""
    return SettingsDialog(settings)


def test_dialog_init(dialog):
    """Test dialog initialization"""
    assert dialog.settings is not None


def test_save_settings(dialog, temp_dir):
    """Test saving settings"""
    # Set test values
    gll_dir = dialog.findChild(QLineEdit, "gll_directory")
    assert gll_dir is not None
    gll_dir.setText(str(temp_dir))

    dialog.accept()

    # Verify settings are saved
    assert dialog.settings.value("gll_files_directory") == str(temp_dir)


def test_browse_directory(dialog, temp_dir, monkeypatch):
    """Test browsing for directory"""

    def mock_get_existing_directory(*args, **kwargs):
        return str(temp_dir)

    monkeypatch.setattr(
        QFileDialog, "getExistingDirectory", mock_get_existing_directory
    )

    # Trigger browse action
    browse_button = dialog.findChild(QPushButton, "browse_gll")
    assert browse_button is not None
    browse_button.click()

    # Verify directory is set
    gll_dir = dialog.findChild(QLineEdit, "gll_directory")
    assert gll_dir is not None
    assert gll_dir.text() == str(temp_dir)
