import pytest
import logging
from unittest.mock import MagicMock

from PySide6.QtWidgets import QMessageBox, QFileDialog

from app import MainWindow


@pytest.fixture
def window(qapp):
    """Create MainWindow instance"""
    return MainWindow()


def test_window_init(window):
    """Test window initialization"""
    assert window.settings is not None
    assert window.process_manager is not None
    assert window.speaker_db is not None


def test_create_menu_bar(window):
    """Test menu bar creation"""
    menu_bar = window.menuBar()
    assert menu_bar is not None
    assert menu_bar.actions() is not None
    assert len(menu_bar.actions()) > 0


def test_open_speaker_management_no_directory(window, monkeypatch):
    """Test opening speaker management with no directory"""
    mock_warning = MagicMock()
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)

    window.settings.setValue("gll_files_directory", "")
    window.open_speaker_management()

    mock_warning.assert_called_once()


def test_open_speaker_management_invalid_directory(window, monkeypatch):
    """Test opening speaker management with invalid directory"""
    mock_warning = MagicMock()
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)

    window.settings.setValue("gll_files_directory", "/invalid/path")
    window.open_speaker_management()

    mock_warning.assert_called_once()


def test_open_speaker_management_no_files(window, monkeypatch, temp_dir):
    """Test opening speaker management with no GLL files"""
    mock_warning = MagicMock()
    monkeypatch.setattr(QMessageBox, "warning", mock_warning)

    window.settings.setValue("gll_files_directory", str(temp_dir))
    window.open_speaker_management()

    mock_warning.assert_called_once()


def test_log_message(window):
    """Test log message handling"""
    test_message = "Test log message"
    window.log_message(logging.INFO, test_message)
    assert test_message in window.log_area.toPlainText()


def test_update_progress(window):
    """Test progress bar update"""
    test_value = 50
    window.update_progress(test_value)
    assert window.progress_bar.value() == test_value


def test_processing_complete(window):
    """Test processing complete handler"""
    window.progress_bar.setValue(-1)  # Set initial value
    window.process_manager.process_complete_signal.emit(True)
    assert window.process_button.isEnabled()
    # assert window.progress_bar.value() == 100


def test_open_files(window, gll_files, monkeypatch):
    """Test opening GLL files"""

    def mock_get_open_file_names(*args, **kwargs):
        return gll_files, "GLL Files (*.GLL *.gll)"

    monkeypatch.setattr(QFileDialog, "getOpenFileNames", mock_get_open_file_names)
    window.open_files()
    assert window.process_button.isEnabled()
    assert window.gll_files == gll_files
