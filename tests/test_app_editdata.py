import pytest

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QTableWidget, QCheckBox, QTableWidgetItem

from app_editdata import MissingSpeakerDialog
from app_db import SpeakerDatabase


@pytest.fixture
def settings():
    """Create test settings"""
    settings = QSettings()
    settings.clear()
    return settings


@pytest.fixture
def dialog(qapp, gll_files, settings, temp_dir):
    """Create MissingSpeakerDialog instance"""
    settings.setValue("gll_files_directory", str(temp_dir))
    return MissingSpeakerDialog(gll_files, settings)


def test_dialog_init(dialog, gll_files):
    """Test dialog initialization"""
    missing_table = dialog.findChild(QTableWidget, "missing_table")
    assert missing_table is not None
    assert missing_table.rowCount() == len(gll_files)


def test_update_existing_table(dialog, temp_dir):
    """Test updating existing speakers table"""
    # Add a test speaker to the database
    db = SpeakerDatabase(str(temp_dir / "test.db"))
    db.save_speaker_data("test.GLL", "Test Speaker", ["config.txt"])

    dialog.update_existing_table()
    table = dialog.findChild(QTableWidget, "existing_table")
    assert table is not None
    assert table.rowCount() > 0


def test_add_config_files(dialog, temp_dir):
    """Test adding config files"""
    # Create test config files
    config_files = []
    for i in range(2):
        file_path = temp_dir / f"config{i}.txt"
        file_path.touch()
        config_files.append(str(file_path))

    table = QTableWidget()
    table.setRowCount(1)
    table.setColumnCount(3)

    dialog.add_config_files(0, table)

    # Verify config files can be added
    assert table.cellWidget(0, 1) is not None


def test_save_all_changes(dialog, temp_dir):
    """Test saving all changes"""
    # Add a test speaker to the database
    db = SpeakerDatabase(str(temp_dir / "test.db"))
    dialog.speaker_db = db

    # Set test data
    missing_table = dialog.findChild(QTableWidget, "missing_table")
    assert missing_table is not None
    missing_table.setRowCount(1)
    missing_table.setItem(0, 0, QTableWidgetItem("test.GLL"))
    missing_table.setItem(0, 1, QTableWidgetItem("Test Speaker"))

    dialog.save_all_changes()

    # Verify data was saved
    data = db.get_speaker_data("test.GLL")
    assert data is not None
    assert data["speaker_name"] == "Test Speaker"


def test_on_skip_changed(dialog, temp_dir):
    """Test skip checkbox handling"""
    # Add a test speaker to the database
    db = SpeakerDatabase(str(temp_dir / "test.db"))
    dialog.speaker_db = db

    # Create a test checkbox
    checkbox = QCheckBox()
    checkbox.setChecked(True)

    dialog.on_missing_skip_changed(0, Qt.Checked)

    # Verify skip status is updated in the database
    data = db.get_speaker_data("test.GLL")
    assert data is not None
    assert data["skip"]
