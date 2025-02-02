import pytest
from unittest.mock import MagicMock

from PySide6.QtCore import QSettings
from app_processmanager import ProcessManager


@pytest.fixture
def settings():
    """Create test settings"""
    settings = QSettings()
    settings.clear()
    return settings


@pytest.fixture
def process_manager(settings):
    """Create ProcessManager instance"""
    return ProcessManager(settings)


def test_process_manager_init(process_manager):
    """Test ProcessManager initialization"""
    assert process_manager.settings is not None


def test_process_gll_files_no_directory(process_manager, caplog):
    """Test processing with no directory set"""
    process_manager.process_complete_signal = MagicMock()
    process_manager.log_signal = MagicMock()

    process_manager.process_gll_files()

    process_manager.process_complete_signal.emit.assert_called_once_with(False)
    log_calls = [call[0] for call in process_manager.log_signal.emit.call_args_list]
    assert any(
        "GLL files directory not set in settings" in call[1] for call in log_calls
    )


def test_process_gll_files_invalid_directory(process_manager, settings, caplog):
    """Test processing with invalid directory"""
    settings.setValue("gll_files_directory", "/invalid/path")
    process_manager.process_complete_signal = MagicMock()
    process_manager.log_signal = MagicMock()

    process_manager.process_gll_files()

    process_manager.process_complete_signal.emit.assert_called_once_with(False)
    log_calls = [call[0] for call in process_manager.log_signal.emit.call_args_list]
    assert any("Directory does not exist" in call[1] for call in log_calls)


def test_process_gll_files_no_files(process_manager, settings, temp_dir, caplog):
    """Test processing with no GLL files"""
    settings.setValue("gll_files_directory", str(temp_dir))
    process_manager.process_complete_signal = MagicMock()
    process_manager.log_signal = MagicMock()

    process_manager.process_gll_files()

    process_manager.process_complete_signal.emit.assert_called_once_with(False)
    log_calls = [call[0] for call in process_manager.log_signal.emit.call_args_list]
    assert any("No GLL files found" in call[1] for call in log_calls)


def test_process_gll_files_with_files(process_manager, settings, gll_files, temp_dir):
    """Test processing with GLL files"""
    settings.setValue("gll_files_directory", str(temp_dir))
    process_manager.process_complete_signal = MagicMock()
    process_manager.log_signal = MagicMock()

    process_manager.process_gll_files()

    # Verify log messages
    log_calls = [call[0] for call in process_manager.log_signal.emit.call_args_list]
    assert any("Found 3 GLL files" in call[1] for call in log_calls)


def test_cleanup(process_manager):
    """Test cleanup method"""
    process_manager.cleanup()  # Should not raise any errors
