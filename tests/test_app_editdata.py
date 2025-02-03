import pytest

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QTableWidget,
    QCheckBox,
    QTableWidgetItem,
    QLineEdit,
    QWidget,
    QHBoxLayout,
)

from app_editdata import MissingSpeakerDialog


@pytest.fixture
def settings(temp_dir):
    """Create test settings"""
    settings = QSettings()
    settings.clear()
    settings.setValue("database_path", str(temp_dir / "test.db"))
    settings.setValue("gll_files_directory", str(temp_dir))
    return settings


@pytest.fixture
def dialog(qapp, gll_files, settings, temp_dir):
    """Create MissingSpeakerDialog instance"""
    return MissingSpeakerDialog(gll_files, settings)


def test_dialog_init(dialog, gll_files):
    """Test dialog initialization"""
    missing_table = dialog.findChild(QTableWidget, "missing_table")
    assert missing_table is not None
    assert missing_table.rowCount() == len(gll_files)


def test_update_existing_table(dialog, temp_dir):
    """Test updating existing speakers table"""
    # Add a test speaker to the database
    dialog.speaker_db.save_speaker_data("test.GLL", "Test Speaker", ["config.txt"])

    # Add the GLL file to missing files
    dialog.missing_gll_files.append("test.GLL")

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

    # Add a test speaker to the database
    dialog.speaker_db.save_speaker_data("test.GLL", "Test Speaker", [])

    # Add the GLL file to missing files
    dialog.missing_gll_files.append("test.GLL")
    dialog.missing_table.setRowCount(1)
    dialog.missing_table.setItem(0, 0, QTableWidgetItem("test.GLL"))

    # Add config files
    dialog.add_config_files(0, is_missing=True)

    # Verify config files can be added
    config_btn = dialog.missing_table.cellWidget(0, 2)
    assert config_btn is not None
    assert config_btn.text() == "Add Config Files"


def test_save_all_changes(dialog, temp_dir):
    """Test saving all changes"""
    # Add the GLL file to missing files
    dialog.missing_gll_files.append("test.GLL")
    dialog.missing_table.setRowCount(1)
    dialog.missing_table.setItem(0, 0, QTableWidgetItem("test.GLL"))

    # Set test data
    speaker_input = QLineEdit()
    speaker_input.setText("Test Speaker")
    dialog.missing_table.setCellWidget(0, 1, speaker_input)

    dialog.save_all_changes()

    # Verify data was saved
    data = dialog.speaker_db.get_speaker_data("test.GLL")
    assert data is not None
    assert data["speaker_name"] == "Test Speaker"


def test_on_skip_changed(dialog, temp_dir):
    """Test skip checkbox handling"""
    # Add the GLL file to missing files
    dialog.missing_gll_files.append("test.GLL")
    dialog.missing_table.setRowCount(1)
    dialog.missing_table.setItem(0, 0, QTableWidgetItem("test.GLL"))

    # Set up the skip checkbox
    skip_checkbox = QCheckBox()
    skip_checkbox.setChecked(True)
    skip_cell_widget = QWidget()
    skip_layout = QHBoxLayout(skip_cell_widget)
    skip_layout.addWidget(skip_checkbox)
    skip_layout.setAlignment(Qt.AlignCenter)
    skip_layout.setContentsMargins(0, 0, 0, 0)
    dialog.missing_table.setCellWidget(0, 4, skip_cell_widget)

    # Set test data
    speaker_input = QLineEdit()
    speaker_input.setText("Test Speaker")
    dialog.missing_table.setCellWidget(0, 1, speaker_input)

    # Trigger skip change
    dialog.on_missing_skip_changed(0, Qt.Checked)

    # Save changes
    dialog.save_all_changes()

    # Verify skip status is updated in the database
    data = dialog.speaker_db.get_speaker_data("test.GLL")
    assert data is not None
    assert data["skip"]
