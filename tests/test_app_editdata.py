import logging

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from app_editdata import MissingSpeakerDialog
from database import SpeakerDatabase


@pytest.fixture
def settings(temp_dir):
    """Create test settings"""
    settings = QSettings()
    settings.clear()
    settings.setValue("database_path", str(temp_dir / "test.db"))
    settings.setValue("gll_files_directory", str(temp_dir))
    return settings


@pytest.fixture
def dialog(qapp, temp_dir, settings, db, gll_files):
    """Create a dialog for testing"""
    dialog = MissingSpeakerDialog(
        settings, gll_files, parent=None, test_mode=True, speaker_db=db
    )
    return dialog


def test_dialog_init(dialog, temp_dir):
    """Test dialog initialization"""
    logging.debug("Starting test_dialog_init")
    missing_table = dialog.findChild(QTableWidget, "missing_table")
    logging.debug(f"Missing table found: {missing_table is not None}")
    assert missing_table is not None
    row_count = missing_table.rowCount()
    logging.debug(f"Missing table row count: {row_count}")
    assert row_count == len(dialog.missing_gll_files)
    logging.debug("Finished test_dialog_init")


def test_update_existing_table(dialog, temp_dir):
    """Test updating existing speakers table"""
    # Add a test speaker to the database
    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(test_gll, "Test Speaker", ["config.txt"])

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)

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

    # Add the GLL file to gll_files and missing_gll_files
    if "test.GLL" not in dialog.gll_files:
        dialog.gll_files.append("test.GLL")
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
    # Add the GLL file to gll_files and missing_gll_files
    if "test.GLL" not in dialog.gll_files:
        dialog.gll_files.append("test.GLL")
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
    # Add the GLL file to gll_files and missing_gll_files
    if "test.GLL" not in dialog.gll_files:
        dialog.gll_files.append("test.GLL")
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


def test_edit_config_files_dialog(dialog, temp_dir):
    """Test opening and closing the config files dialog"""
    # Create test config files
    config_files = []
    for i in range(2):
        file_path = temp_dir / f"config{i}.txt"
        file_path.touch()
        config_files.append(str(file_path))

    # Add a test speaker to the database
    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(test_gll, "Test Speaker", config_files)

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    # Get data for the speaker
    data = dialog.existing_speaker_data[0]

    # Open config files dialog
    config_dialog = dialog.edit_config_files(data)
    assert config_dialog is not None

    # Verify config files are displayed
    config_list = config_dialog.findChild(QTableWidget)
    assert config_list is not None
    assert config_list.rowCount() == len(config_files)

    # Close dialog
    config_dialog.reject()


def test_edit_properties_dialog(dialog, temp_dir):
    """Test opening and closing the properties dialog"""
    # Add a test speaker to the database with properties
    test_properties = {
        "sensitivity": 90.0,
        "impedance": 8.0,
        "weight": 10.5,
        "height": 20.0,
        "width": 15.0,
        "depth": 12.5,
    }

    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(test_gll, "Test Speaker", [], **test_properties)

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    # Open properties dialog directly with test data
    properties_dialog = dialog.edit_speaker_properties(
        {"gll_file": test_gll, "speaker_name": "Test Speaker", **test_properties}
    )

    # Verify dialog was created
    assert properties_dialog is not None

    # Verify initial values
    assert (
        abs(properties_dialog.sensitivity.value() - test_properties["sensitivity"])
        < 0.1
    )
    assert abs(properties_dialog.impedance.value() - test_properties["impedance"]) < 0.1
    assert abs(properties_dialog.weight.value() - test_properties["weight"]) < 0.1
    assert abs(properties_dialog.height.value() - test_properties["height"]) < 0.1
    assert abs(properties_dialog.width.value() - test_properties["width"]) < 0.1
    assert abs(properties_dialog.depth.value() - test_properties["depth"]) < 0.1

    # Close dialog
    if not dialog.test_mode:
        properties_dialog.accept()


def test_save_properties(dialog, temp_dir):
    """Test saving speaker properties"""
    # Add a test speaker to the database with initial properties
    initial_properties = {
        "sensitivity": 50.0,
        "impedance": 8.0,
        "weight": 10.0,
        "height": 20.0,
        "width": 15.0,
        "depth": 12.0,
    }

    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(
        test_gll, "Test Speaker", [], **initial_properties
    )

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    # Get data for the speaker
    data = dialog.existing_speaker_data[0]

    # Open properties dialog
    properties_dialog = dialog.edit_speaker_properties(data)
    assert properties_dialog is not None

    # Verify dialog shows correct values
    assert (
        abs(properties_dialog.sensitivity.value() - initial_properties["sensitivity"])
        < 0.1
    )
    assert (
        abs(properties_dialog.impedance.value() - initial_properties["impedance"]) < 0.1
    )
    assert abs(properties_dialog.weight.value() - initial_properties["weight"]) < 0.1
    assert abs(properties_dialog.height.value() - initial_properties["height"]) < 0.1
    assert abs(properties_dialog.width.value() - initial_properties["width"]) < 0.1
    assert abs(properties_dialog.depth.value() - initial_properties["depth"]) < 0.1

    # Set new properties
    new_properties = {
        "sensitivity": 90.0,
        "impedance": 8.0,
        "weight": 10.5,
        "height": 20.0,
        "width": 15.0,
        "depth": 12.5,
    }

    # Set values in dialog
    properties_dialog.sensitivity.setValue(new_properties["sensitivity"])
    properties_dialog.impedance.setValue(new_properties["impedance"])
    properties_dialog.weight.setValue(new_properties["weight"])
    properties_dialog.height.setValue(new_properties["height"])
    properties_dialog.width.setValue(new_properties["width"])
    properties_dialog.depth.setValue(new_properties["depth"])

    if not dialog.test_mode:
        properties_dialog.accept()

        # Verify properties were saved
        saved_data = dialog.speaker_db.get_speaker_data("test.GLL")
        assert saved_data is not None
        for key, value in new_properties.items():
            assert abs(saved_data[key] - value) < 0.1


def test_save_config_files(dialog, temp_dir):
    """Test saving config files"""
    # Create test config files
    config_files = []
    for i in range(2):
        file_path = temp_dir / f"config{i}.txt"
        file_path.touch()
        config_files.append(str(file_path))

    # Add a test speaker to the database
    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(test_gll, "Test Speaker", [])

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    # Get data for the speaker
    data = dialog.existing_speaker_data[0]

    # Open config files dialog
    config_dialog = dialog.edit_config_files(data)
    assert config_dialog is not None

    # Add config files
    for file_path in config_files:
        config_dialog.add_config_file(file_path)

    # Save config files
    config_dialog.accept()

    # Save changes to database
    data["config_files"] = config_dialog.get_config_files()
    dialog.speaker_db.save_speaker_data(
        data["gll_file"], data["speaker_name"], data["config_files"]
    )

    # Verify config files are saved in database
    saved_data = dialog.speaker_db.get_speaker_data("test.GLL")
    assert saved_data is not None
    assert len(saved_data["config_files"]) == len(config_files)
    for file_path in config_files:
        assert file_path in saved_data["config_files"]


def test_edit_existing_speaker(dialog, temp_dir):
    """Test editing an existing speaker"""
    # Add a test speaker to the database
    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(test_gll, "Test Speaker", ["config.txt"])

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    # Verify speaker is in table
    table = dialog.findChild(QTableWidget, "existing_table")
    assert table is not None
    assert table.rowCount() == 1

    # Edit speaker name
    speaker_input = table.cellWidget(0, 1)
    assert speaker_input is not None
    speaker_input.setText("Updated Speaker")

    # Save changes
    dialog.save_all_changes()

    # Verify changes are saved in database
    data = dialog.speaker_db.get_speaker_data("test.GLL")
    assert data is not None
    assert data["speaker_name"] == "Updated Speaker"


def test_skip_existing_speaker(dialog, temp_dir):
    """Test skipping an existing speaker"""
    # Add a test speaker to the database
    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(test_gll, "Test Speaker", ["config.txt"])

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    # Verify speaker is in table
    table = dialog.findChild(QTableWidget, "existing_table")
    assert table is not None
    assert table.rowCount() == 1

    # Find skip checkbox
    skip_cell_widget = table.cellWidget(0, 4)
    assert skip_cell_widget is not None
    skip_checkbox = skip_cell_widget.findChild(QCheckBox)
    assert skip_checkbox is not None

    # Toggle skip checkbox
    skip_checkbox.setChecked(True)

    # Save changes
    dialog.save_all_changes()

    # Verify skip status is updated in database
    data = dialog.speaker_db.get_speaker_data("test.GLL")
    assert data is not None
    assert data["skip"]


def test_existing_speaker_widgets(dialog, temp_dir):
    """Test widgets in existing speakers table"""
    # Add a test speaker first
    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(
        test_gll, "Test Speaker", ["config.txt"], sensitivity=90.0, impedance=8.0
    )

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    existing_table = dialog.findChild(QTableWidget, "existing_table")
    assert existing_table.rowCount() > 0

    # Check table widgets
    assert existing_table.item(0, 0).text() == "test.GLL"
    assert isinstance(existing_table.cellWidget(0, 1), QLineEdit)
    assert isinstance(existing_table.cellWidget(0, 2), QPushButton)
    assert isinstance(existing_table.cellWidget(0, 3), QPushButton)
    assert isinstance(existing_table.cellWidget(0, 4), QWidget)
    assert isinstance(existing_table.cellWidget(0, 5), QPushButton)

    # Test properties button
    properties_btn = existing_table.cellWidget(0, 3)
    assert isinstance(properties_btn, QPushButton)
    assert properties_btn.text() == "Properties"

    # Simulate click and verify properties dialog opens
    properties_dialog = dialog.edit_speaker_properties(
        {"gll_file": "test.GLL", "speaker_name": "Test Speaker"}
    )
    assert properties_dialog is not None
    assert abs(properties_dialog.sensitivity.value() - 90.0) < 0.1
    assert abs(properties_dialog.impedance.value() - 8.0) < 0.1

    # Test updating properties
    new_values = {
        "sensitivity": 92.0,
        "impedance": 4.0,
        "weight": 15.0,
        "height": 25.0,
        "width": 18.0,
        "depth": 14.0,
    }

    properties_dialog.sensitivity.setValue(new_values["sensitivity"])
    properties_dialog.impedance.setValue(new_values["impedance"])
    properties_dialog.weight.setValue(new_values["weight"])
    properties_dialog.height.setValue(new_values["height"])
    properties_dialog.width.setValue(new_values["width"])
    properties_dialog.depth.setValue(new_values["depth"])

    if not dialog.test_mode:
        properties_dialog.accept()

        # Verify properties were saved
        saved_data = dialog.speaker_db.get_speaker_data("test.GLL")
        assert abs(saved_data["sensitivity"] - new_values["sensitivity"]) < 0.1
        assert abs(saved_data["impedance"] - new_values["impedance"]) < 0.1
        assert abs(saved_data["weight"] - new_values["weight"]) < 0.1
        assert abs(saved_data["height"] - new_values["height"]) < 0.1
        assert abs(saved_data["width"] - new_values["width"]) < 0.1
        assert abs(saved_data["depth"] - new_values["depth"]) < 0.1


def test_edit_missing_properties_dialog(dialog, temp_dir):
    """Test editing properties for a missing speaker"""
    if not dialog.missing_gll_files:
        return

    row = 0

    # Open properties dialog for first missing speaker
    dialog.edit_missing_properties(row)

    # Set test properties
    test_properties = {
        "sensitivity": 90.0,
        "impedance": 8.0,
        "weight": 10.5,
        "height": 20.0,
        "width": 15.0,
        "depth": 12.5,
    }
    dialog.missing_properties[row] = test_properties

    # Verify properties were stored correctly
    assert isinstance(dialog.missing_properties[row], dict)
    for key in ["sensitivity", "impedance", "weight", "height", "width", "depth"]:
        assert key in dialog.missing_properties[row]
        assert abs(dialog.missing_properties[row][key] - test_properties[key]) < 0.1


def test_save_missing_speaker_with_properties(dialog, temp_dir):
    """Test saving a missing speaker with properties"""
    if not dialog.missing_gll_files:
        return

    row = 0
    gll_file = dialog.missing_gll_files[row]

    # Set speaker name
    speaker_input = dialog.missing_table.cellWidget(row, 1)
    speaker_input.setText("Test Speaker")

    # Set properties
    test_properties = {
        "sensitivity": 88.0,
        "impedance": 4.0,
        "weight": 15.5,
        "height": 30.0,
        "width": 20.0,
        "depth": 25.0,
    }
    dialog.missing_properties[gll_file] = test_properties

    # Save changes
    dialog.save_all_changes()

    # Verify saved data
    saved_data = dialog.speaker_db.get_speaker_data(gll_file)
    assert saved_data is not None
    assert saved_data["speaker_name"] == "Test Speaker"
    for key, value in test_properties.items():
        assert abs(saved_data[key] - value) < 0.1


def test_edit_existing_speaker_properties(dialog, temp_dir):
    """Test editing properties for an existing speaker"""
    # Add a test speaker
    test_data = {
        "gll_file": "test.GLL",
        "speaker_name": "Test Speaker",
        "config_files": [],
        "sensitivity": 90.0,
        "impedance": 8.0,
        "weight": 10.0,
        "height": 20.0,
        "width": 15.0,
        "depth": 12.0,
        "skip": False,
    }

    dialog.speaker_db.save_speaker_data(
        test_data["gll_file"],
        test_data["speaker_name"],
        test_data["config_files"],
        sensitivity=test_data["sensitivity"],
        impedance=test_data["impedance"],
        weight=test_data["weight"],
        height=test_data["height"],
        width=test_data["width"],
        depth=test_data["depth"],
    )

    # Add the GLL file to gll_files and missing_gll_files
    if test_data["gll_file"] not in dialog.gll_files:
        dialog.gll_files.append(test_data["gll_file"])
    dialog.missing_gll_files.append(test_data["gll_file"])
    dialog.update_existing_table()

    # Find the speaker in the table
    existing_table = dialog.findChild(QTableWidget, "existing_table")
    row = None
    for r in range(existing_table.rowCount()):
        if existing_table.item(r, 0).text() == test_data["gll_file"]:
            row = r
            break

    assert row is not None

    # Get the properties button and simulate click
    properties_btn = existing_table.cellWidget(row, 3)
    assert isinstance(properties_btn, QPushButton)
    assert properties_btn.text() == "Properties"

    # Simulate button click by calling the connected method
    properties_dialog = dialog.edit_speaker_properties(test_data)
    assert properties_dialog is not None

    # Verify initial values
    assert abs(properties_dialog.sensitivity.value() - test_data["sensitivity"]) < 0.1
    assert abs(properties_dialog.impedance.value() - test_data["impedance"]) < 0.1
    assert abs(properties_dialog.weight.value() - test_data["weight"]) < 0.1
    assert abs(properties_dialog.height.value() - test_data["height"]) < 0.1
    assert abs(properties_dialog.width.value() - test_data["width"]) < 0.1
    assert abs(properties_dialog.depth.value() - test_data["depth"]) < 0.1

    # Test modifying values
    new_values = {
        "sensitivity": 92.0,
        "impedance": 4.0,
        "weight": 12.0,
        "height": 25.0,
        "width": 18.0,
        "depth": 14.0,
    }

    properties_dialog.sensitivity.setValue(new_values["sensitivity"])
    properties_dialog.impedance.setValue(new_values["impedance"])
    properties_dialog.weight.setValue(new_values["weight"])
    properties_dialog.height.setValue(new_values["height"])
    properties_dialog.width.setValue(new_values["width"])
    properties_dialog.depth.setValue(new_values["depth"])

    if not dialog.test_mode:
        properties_dialog.accept()

        # Verify properties were saved
        saved_data = dialog.speaker_db.get_speaker_data(test_data["gll_file"])
        assert saved_data is not None
        for key, value in new_values.items():
            assert abs(saved_data[key] - value) < 0.1


def test_delete_speaker(dialog, temp_dir):
    """Test deleting a speaker"""
    # Add a test speaker to the database
    test_gll = "test.GLL"
    dialog.speaker_db.save_speaker_data(test_gll, "Test Speaker", ["config.txt"])

    # Add the GLL file to gll_files and missing_gll_files
    if test_gll not in dialog.gll_files:
        dialog.gll_files.append(test_gll)
    dialog.missing_gll_files.append(test_gll)
    dialog.update_existing_table()

    # Get data for the speaker
    data = dialog.existing_speaker_data[0]

    # Delete speaker
    dialog.delete_speaker(data)

    # Verify speaker is removed from table and database
    assert dialog.existing_table.rowCount() == 0
    assert dialog.speaker_db.get_speaker_data("test.GLL") is None


def test_delete_speaker_cancel(qapp, temp_dir, monkeypatch):
    """Test canceling speaker deletion"""
    # Create test database
    db_path = temp_dir / "test_db.json"
    speaker_db = SpeakerDatabase(db_path)

    # Add test speaker
    gll_file = "test.gll"
    speaker_name = "Test Speaker"
    config_files = ["config1.txt", "config2.txt"]
    speaker_db.save_speaker_data(gll_file, speaker_name, config_files)

    # Create settings
    settings = QSettings()
    settings.setValue("database_path", str(db_path))

    # Create dialog with test_mode=False to test confirmation
    dialog = MissingSpeakerDialog(
        settings, [gll_file], parent=None, test_mode=False, speaker_db=speaker_db
    )
    dialog.missing_gll_files = [gll_file]  # Set missing files
    dialog.update_existing_table()

    # Mock QMessageBox to return No
    def mock_exec(self):
        return QMessageBox.No

    monkeypatch.setattr(QMessageBox, "exec", mock_exec)

    # Get initial row count
    initial_count = dialog.existing_table.rowCount()
    assert initial_count > 0  # Verify speaker is in table

    # Get speaker data
    data = {"gll_file": gll_file, "speaker_name": speaker_name}

    # Try to delete speaker
    dialog.delete_speaker(data)

    # Verify speaker was not deleted
    assert dialog.existing_table.rowCount() == initial_count
    assert speaker_db.get_speaker_data(gll_file) is not None


def test_suggest_speaker_name(dialog):
    """Test speaker name suggestion functionality"""
    test_path = "/path/to/Brand/Model.GLL"
    suggested_name = dialog.suggest_speaker_name(test_path)
    assert suggested_name == "Brand Model"


def test_missing_table_initialization(dialog, temp_dir):
    """Test initialization of missing speakers table"""
    missing_table = dialog.findChild(QTableWidget, "missing_table")
    if dialog.missing_gll_files:
        assert missing_table is not None
        assert missing_table.columnCount() == 5
        assert missing_table.horizontalHeaderItem(0).text() == "GLL File"
        assert missing_table.horizontalHeaderItem(1).text() == "Speaker Name"
        assert missing_table.horizontalHeaderItem(2).text() == "Config Files"
        assert missing_table.horizontalHeaderItem(3).text() == "Properties"
        assert missing_table.horizontalHeaderItem(4).text() == "Skip"


def test_existing_table_initialization(dialog):
    """Test initialization of existing speakers table"""
    existing_table = dialog.findChild(QTableWidget, "existing_table")
    assert existing_table is not None
    assert existing_table.columnCount() == 6
    assert existing_table.horizontalHeaderItem(0).text() == "GLL File"
    assert existing_table.horizontalHeaderItem(1).text() == "Speaker Name"
    assert existing_table.horizontalHeaderItem(2).text() == "Config Files"
    assert existing_table.horizontalHeaderItem(3).text() == "Properties"
    assert existing_table.horizontalHeaderItem(4).text() == "Skip"
    assert existing_table.horizontalHeaderItem(5).text() == "Actions"


def test_missing_speaker_widgets(dialog, temp_dir):
    """Test widgets in missing speakers table"""
    if not dialog.missing_gll_files:
        return

    missing_table = dialog.findChild(QTableWidget, "missing_table")
    first_row = 0

    # Test speaker name input
    speaker_input = missing_table.cellWidget(first_row, 1)
    assert isinstance(speaker_input, QLineEdit)
    assert speaker_input.text() == dialog.suggest_speaker_name(
        dialog.missing_gll_files[0]
    )

    # Test config files button
    config_btn = missing_table.cellWidget(first_row, 2)
    assert isinstance(config_btn, QPushButton)
    assert config_btn.text() == "Add Config Files"

    # Test properties button
    properties_btn = missing_table.cellWidget(first_row, 3)
    assert isinstance(properties_btn, QPushButton)
    assert properties_btn.text() == "Edit"

    # Test skip checkbox
    skip_widget = missing_table.cellWidget(first_row, 4)
    assert isinstance(skip_widget, QWidget)
    skip_checkbox = skip_widget.findChild(QCheckBox)
    assert isinstance(skip_checkbox, QCheckBox)
    assert not skip_checkbox.isChecked()
