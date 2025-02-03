import os
import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QCheckBox,
    QWidget,
)

from database import SpeakerDatabase
from app_speaker_properties import SpeakerPropertiesDialog


class MissingSpeakerDialog(QDialog):
    def __init__(self, settings, gll_files, parent=None, test_mode=False):
        super().__init__(parent)
        logging.debug("Initializing MissingSpeakerDialog")
        self.setWindowTitle("Speaker Data Management")
        self.resize(1000, 800)
        self.settings = settings
        self.test_mode = test_mode
        logging.debug(f"Settings: {settings}")
        logging.debug(f"Test mode is {'enabled' if self.test_mode else 'disabled'}")

        # Main layout
        main_layout = QVBoxLayout()

        # Speaker Database
        self.speaker_db = SpeakerDatabase(settings.value("database_path"))
        logging.debug("Created SpeakerDatabase")

        # Separate lists for missing and existing speaker data
        self.missing_gll_files = []
        self.existing_speaker_data = []

        # Categorize GLL files
        logging.debug(f"Processing {len(gll_files)} GLL files")
        for gll_file in gll_files:
            logging.debug(f"Processing file: {gll_file}")
            speaker_data = self.speaker_db.get_speaker_data(gll_file)
            if not speaker_data:
                logging.debug(f"No speaker data found for {gll_file}")
                self.missing_gll_files.append(gll_file)
            else:
                logging.debug(f"Found speaker data for {gll_file}")
                self.existing_speaker_data.append(
                    {
                        "gll_file": gll_file,
                        "speaker_name": speaker_data["speaker_name"],
                        "config_files": speaker_data["config_files"],
                        "skip": speaker_data.get("skip", False),
                    }
                )

        # Missing Speaker Section
        if self.missing_gll_files:
            missing_label = QLabel("Missing Speaker Information:")
            missing_label.setObjectName("missing_label")
            main_layout.addWidget(missing_label)

            # Missing Speaker Table
            self.missing_table = QTableWidget()
            self.missing_table.setObjectName("missing_table")
            self.missing_table.setColumnCount(5)
            self.missing_table.setHorizontalHeaderLabels(
                ["GLL File", "Speaker Name", "Config Files", "Properties", "Skip"]
            )
            self.missing_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.Stretch
            )
            logging.debug("Initialized missing_table")

            self.missing_table.setRowCount(len(self.missing_gll_files))
            logging.debug(
                f"Set row count of missing_table to {len(self.missing_gll_files)}"
            )
            self.missing_config_files = [[] for _ in self.missing_gll_files]
            self.missing_skip_states = [False for _ in self.missing_gll_files]
            self.missing_properties = {}  # Change from list to dict

            for row, gll_file in enumerate(self.missing_gll_files):
                logging.debug(f"Adding row for {gll_file}")
                # GLL File column
                file_item = QTableWidgetItem(gll_file)
                file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
                self.missing_table.setItem(row, 0, file_item)

                # Speaker Name column
                speaker_input = QLineEdit()
                speaker_input.setObjectName("speaker_input")
                speaker_input.setText(self.suggest_speaker_name(gll_file))
                self.missing_table.setCellWidget(row, 1, speaker_input)

                # Config Files column
                config_btn = QPushButton("Add Config Files")
                config_btn.setObjectName("config_btn")
                config_btn.clicked.connect(
                    lambda checked, r=row: self.add_config_files(r, is_missing=True)
                )
                self.missing_table.setCellWidget(row, 2, config_btn)

                # Properties column
                properties_btn = QPushButton("Edit Properties")
                properties_btn.setObjectName("properties_btn")
                properties_btn.clicked.connect(
                    lambda checked, row=row: self.edit_missing_properties(row)
                )
                logging.debug(f"Created properties button for row {row}")
                self.missing_table.setCellWidget(row, 3, properties_btn)

                # Skip checkbox column
                skip_checkbox = QCheckBox()
                skip_checkbox.setObjectName("skip_checkbox")
                skip_checkbox.setChecked(False)
                skip_checkbox.stateChanged.connect(
                    lambda state, r=row: self.on_missing_skip_changed(r, state)
                )
                skip_cell_widget = QWidget()
                skip_layout = QHBoxLayout(skip_cell_widget)
                skip_layout.addWidget(skip_checkbox)
                skip_layout.setAlignment(Qt.AlignCenter)
                skip_layout.setContentsMargins(0, 0, 0, 0)
                self.missing_table.setCellWidget(row, 4, skip_cell_widget)

            main_layout.addWidget(self.missing_table)

        # Existing Speaker Section
        existing_label = QLabel("Existing Speaker Information:")
        existing_label.setObjectName("existing_label")
        main_layout.addWidget(existing_label)

        # Existing Speaker Table
        self.existing_table = QTableWidget()
        self.existing_table.setObjectName("existing_table")
        self.existing_table.setColumnCount(6)
        self.existing_table.setHorizontalHeaderLabels(
            [
                "GLL File",
                "Speaker Name",
                "Config Files",
                "Properties",
                "Skip",
                "Actions",
            ]
        )
        self.existing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        logging.debug("Initialized existing_table")

        main_layout.addWidget(self.existing_table)

        # Populate existing table
        self.update_existing_table()

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("save_btn")
        save_btn.clicked.connect(self.save_all_changes)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancel_btn")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def suggest_speaker_name(self, gll_file):
        """Suggest a speaker name based on the GLL file path.
        The last directory in the path is the brand name and the file name (without extension) is the model name."""
        logging.debug(f"Suggesting speaker name for GLL file: {gll_file}")

        # Get the directory path and file name
        path = os.path.dirname(gll_file)
        file_name = os.path.basename(gll_file)
        logging.debug(f"Path: {path}, File name: {file_name}")

        # Get the brand name (last directory in path)
        brand = os.path.basename(path)
        logging.debug(f"Brand name (from last directory): {brand}")

        # Get the model name (file name without .GLL extension)
        model = os.path.splitext(file_name)[0]
        logging.debug(f"Model name (without extension): {model}")

        # Combine brand and model
        suggested_name = f"{brand} {model}"
        logging.debug(f"Suggested speaker name: {suggested_name}")

        return suggested_name

    def update_existing_table(self):
        """Update existing speakers table"""
        logging.debug("Updating existing_table")
        self.existing_table.setRowCount(0)
        self.existing_speaker_data = []

        for gll_file in self.missing_gll_files:
            data = self.speaker_db.get_speaker_data(gll_file)
            if not data:
                continue

            # Add gll_file to data dict if not present
            data["gll_file"] = gll_file
            self.existing_speaker_data.append(data)
            row = self.existing_table.rowCount()
            self.existing_table.insertRow(row)
            logging.debug(f"Added row for {gll_file}")

            # GLL File column
            self.existing_table.setItem(row, 0, QTableWidgetItem(gll_file))

            # Speaker Name column
            speaker_input = QLineEdit()
            speaker_input.setText(data["speaker_name"])
            speaker_input.setObjectName(f"speaker_name_{row}")
            self.existing_table.setCellWidget(row, 1, speaker_input)

            # Config Files column
            config_btn = QPushButton(f"Config Files ({len(data['config_files'])})")
            config_btn.clicked.connect(
                lambda checked, d=data: self.edit_config_files(d)
            )
            self.existing_table.setCellWidget(row, 2, config_btn)

            # Properties column
            properties_btn = QPushButton("Properties")
            properties_btn.clicked.connect(
                lambda checked, d=data: self.edit_speaker_properties(d)
            )
            self.existing_table.setCellWidget(row, 3, properties_btn)

            # Skip column
            skip_cell_widget = QWidget()
            skip_layout = QHBoxLayout(skip_cell_widget)
            skip_checkbox = QCheckBox()
            skip_checkbox.setChecked(data.get("skip", False))
            skip_checkbox.stateChanged.connect(
                lambda state, r=row: self.on_existing_skip_changed(r, state)
            )
            skip_layout.addWidget(skip_checkbox)
            skip_layout.setAlignment(Qt.AlignCenter)
            skip_layout.setContentsMargins(0, 0, 0, 0)
            self.existing_table.setCellWidget(row, 4, skip_cell_widget)

            # Add delete button
            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, d=data: self.delete_speaker(d))
            self.existing_table.setCellWidget(row, 5, delete_btn)

    def edit_config_files(self, data):
        """Open dialog to edit config files for an existing entry"""
        config_dialog = ConfigFilesDialog(data["config_files"], parent=self)

        if not self.test_mode:
            if config_dialog.exec() == QDialog.Accepted:
                # Update config files
                data["config_files"] = config_dialog.get_config_files()

                # Update database
                current_data = self.speaker_db.get_speaker_data(data["gll_file"])
                if current_data:
                    self.speaker_db.save_speaker_data(
                        data["gll_file"],
                        data["speaker_name"],
                        data["config_files"],
                        skip=current_data.get("skip", False),
                        sensitivity=current_data.get("sensitivity"),
                        impedance=current_data.get("impedance"),
                        weight=current_data.get("weight"),
                        height=current_data.get("height"),
                        width=current_data.get("width"),
                        depth=current_data.get("depth"),
                    )
                else:
                    self.speaker_db.save_speaker_data(
                        data["gll_file"], data["speaker_name"], data["config_files"]
                    )

                # Update button text
                for row in range(self.existing_table.rowCount()):
                    if self.existing_table.item(row, 0).text() == data["gll_file"]:
                        btn = self.existing_table.cellWidget(row, 2)
                        btn.setText(f"Config Files ({len(data['config_files'])})")
                        break

        return config_dialog

    def add_config_files(self, row, is_missing=False):
        """Open file dialog to select config files"""
        # Validate row index
        if is_missing:
            if row < 0 or row >= len(self.missing_gll_files):
                logging.error(f"Invalid row index {row} for missing table")
                return
        else:
            if row < 0 or row >= len(self.existing_speaker_data):
                logging.error(f"Invalid row index {row} for existing table")
                return

        # Use non-modal dialog
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Config Files")
        file_dialog.setNameFilter("Config Files (*.xglc);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Force Qt dialog

        # Get initial directory from GLL file if possible
        if is_missing:
            gll_file = self.missing_table.item(row, 0).text()
        else:
            gll_file = self.existing_table.item(row, 0).text()

        initial_dir = os.path.dirname(gll_file) if gll_file else ""
        file_dialog.setDirectory(initial_dir)

        def handle_files():
            if file_dialog.result() == QDialog.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    if is_missing:
                        self.missing_config_files[row].extend(selected_files)
                        config_btn = self.missing_table.cellWidget(row, 2)
                        config_btn.setText(
                            f"Config Files ({len(self.missing_config_files[row])})"
                        )
                    else:
                        data = self.existing_speaker_data[row]
                        data["config_files"].extend(selected_files)
                        config_btn = self.existing_table.cellWidget(row, 2)
                        config_btn.setText(
                            f"Config Files ({len(data['config_files'])})"
                        )

        file_dialog.finished.connect(handle_files)
        file_dialog.open()

    def edit_speaker_properties(self, data):
        """Edit speaker properties"""
        # Get current properties from database
        current_data = self.speaker_db.get_speaker_data(data["gll_file"])
        if current_data:
            data.update(current_data)

        dialog = SpeakerPropertiesDialog(
            speaker_name=data.get("speaker_name", ""),
            sensitivity=data.get("sensitivity"),
            impedance=data.get("impedance"),
            weight=data.get("weight"),
            height=data.get("height"),
            width=data.get("width"),
            depth=data.get("depth"),
            parent=self,
            test_mode=self.test_mode,
        )

        if not self.test_mode:
            if dialog.exec() == QDialog.Accepted:
                # Update database
                self.speaker_db.save_speaker_data(
                    data["gll_file"],
                    data["speaker_name"],
                    data["config_files"],
                    data.get("skip", False),
                    float(dialog.sensitivity.value()),
                    float(dialog.impedance.value()),
                    float(dialog.weight.value()),
                    float(dialog.height.value()),
                    float(dialog.width.value()),
                    float(dialog.depth.value()),
                )
                self.update_existing_table()

        return dialog

    def add_new_config_file(self, config_table):
        """Add a new config file to the table"""
        print("Starting add_new_config_file")  # Debug print

        # Get the GLL file path to determine directory
        current_row = self.existing_table.currentRow()
        if current_row >= 0:
            gll_file = self.existing_table.item(current_row, 0).text()
            initial_dir = os.path.dirname(gll_file) if gll_file else ""
        else:
            initial_dir = ""

        print(f"Initial dir: {initial_dir}")  # Debug print

        # Create and configure the file dialog
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Config File")
        file_dialog.setDirectory(initial_dir)
        file_dialog.setNameFilter("Config Files (*.xglc);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Force Qt dialog

        if file_dialog.exec() == QDialog.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                print(f"Selected file: {file_path}")  # Debug print

                row = config_table.rowCount()
                config_table.insertRow(row)
                logging.debug("Added row to config_table")

                # Path
                path_item = QTableWidgetItem(file_path)
                path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
                config_table.setItem(row, 0, path_item)

                # Remove button
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(
                    lambda checked, r=row: self.remove_config_file(config_table, r)
                )
                config_table.setCellWidget(row, 1, remove_btn)

                print("Added new row to table")  # Debug print

    def remove_config_file(self, config_table, row):
        """Remove a config file from the table"""
        config_table.removeRow(row)

    def delete_speaker(self, data):
        """Delete speaker from database"""
        if not self.test_mode:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Delete Speaker")
            msg_box.setText(
                f"Are you sure you want to delete speaker {data['speaker_name']}?"
            )
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            if msg_box.exec() != QMessageBox.Yes:
                return

        # Delete from database
        self.speaker_db.delete_speaker(data["gll_file"])

        # Update tables
        self.update_existing_table()

    def on_missing_skip_changed(self, row, state):
        """Handle skip checkbox state change for missing entries"""
        self.missing_skip_states[row] = bool(state)

    def on_existing_skip_changed(self, row, state):
        """Handle skip checkbox state change for existing entries"""
        data = self.existing_speaker_data[row]
        data["skip"] = bool(state)

    def edit_missing_properties(self, row):
        """Open dialog to edit properties for a missing speaker"""
        logging.debug(f"Opening properties dialog for missing speaker at row {row}")

        gll_file = self.missing_gll_files[row]
        speaker_name = self.missing_table.cellWidget(row, 1).text()
        logging.debug(f"GLL file: {gll_file}, Current speaker name: {speaker_name}")
        logging.debug(
            f"Current properties: {self.missing_properties.get(gll_file, {})}"
        )

        try:
            # Create a dialog with current properties
            dialog = SpeakerPropertiesDialog(
                speaker_name=speaker_name,
                sensitivity=self.missing_properties.get(gll_file, {}).get(
                    "sensitivity"
                ),
                impedance=self.missing_properties.get(gll_file, {}).get("impedance"),
                weight=self.missing_properties.get(gll_file, {}).get("weight"),
                height=self.missing_properties.get(gll_file, {}).get("height"),
                width=self.missing_properties.get(gll_file, {}).get("width"),
                depth=self.missing_properties.get(gll_file, {}).get("depth"),
                parent=self,
                test_mode=self.test_mode,
            )
            logging.debug("Created SpeakerPropertiesDialog")

            result = dialog.exec()
            logging.debug(f"Dialog result: {result}")

            if result == QDialog.Accepted:
                # Store the properties
                new_properties = {
                    "sensitivity": float(dialog.sensitivity.value()),
                    "impedance": float(dialog.impedance.value()),
                    "weight": float(dialog.weight.value()),
                    "height": float(dialog.height.value()),
                    "width": float(dialog.width.value()),
                    "depth": float(dialog.depth.value()),
                }
                self.missing_properties[gll_file] = new_properties
                logging.debug(
                    f"Updated properties for missing speaker {speaker_name}: {new_properties}"
                )
            else:
                logging.debug("Properties dialog was cancelled")

        except Exception as e:
            logging.error(f"Error in edit_missing_properties: {str(e)}", exc_info=True)
            QMessageBox.warning(self, "Error", f"Failed to edit properties: {str(e)}")

    def save_all_changes(self):
        """Save all changes to the database"""
        # Save missing speakers
        for row in range(self.missing_table.rowCount()):
            gll_file = self.missing_table.item(row, 0).text()
            speaker_input = self.missing_table.cellWidget(row, 1)
            if not speaker_input:
                continue

            speaker_name = speaker_input.text()
            if not speaker_name:
                continue

            # Get config files
            config_files = []

            # Get skip status
            skip_cell_widget = self.missing_table.cellWidget(row, 4)
            if skip_cell_widget:
                skip_checkbox = skip_cell_widget.findChild(QCheckBox)
                skip = skip_checkbox.isChecked() if skip_checkbox else False
            else:
                skip = False

            # Get properties
            properties = self.missing_properties.get(gll_file, {})

            # Save to database
            self.speaker_db.save_speaker_data(
                gll_file,
                speaker_name,
                config_files,
                skip=skip,
                sensitivity=properties.get("sensitivity"),
                impedance=properties.get("impedance"),
                weight=properties.get("weight"),
                height=properties.get("height"),
                width=properties.get("width"),
                depth=properties.get("depth"),
            )

        # Save existing speakers
        for row in range(self.existing_table.rowCount()):
            gll_file = self.existing_table.item(row, 0).text()
            speaker_input = self.existing_table.cellWidget(row, 1)
            if not speaker_input:
                continue

            speaker_name = speaker_input.text()
            if not speaker_name:
                continue

            # Get skip status
            skip_cell_widget = self.existing_table.cellWidget(row, 4)
            if skip_cell_widget:
                skip_checkbox = skip_cell_widget.findChild(QCheckBox)
                skip = skip_checkbox.isChecked() if skip_checkbox else False
            else:
                skip = False

            # Get current data from database to preserve other fields
            current_data = self.speaker_db.get_speaker_data(gll_file)
            if current_data:
                self.speaker_db.save_speaker_data(
                    gll_file,
                    speaker_name,
                    current_data.get("config_files", []),
                    skip=skip,
                    sensitivity=current_data.get("sensitivity"),
                    impedance=current_data.get("impedance"),
                    weight=current_data.get("weight"),
                    height=current_data.get("height"),
                    width=current_data.get("width"),
                    depth=current_data.get("depth"),
                )
            else:
                self.speaker_db.save_speaker_data(gll_file, speaker_name, [], skip=skip)

        self.update_existing_table()
        self.accept()


class ConfigFilesDialog(QDialog):
    def __init__(self, config_files, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Config Files")
        self.resize(600, 400)

        layout = QVBoxLayout()

        # Table for config files
        self.config_table = QTableWidget()
        self.config_table.setColumnCount(2)
        self.config_table.setHorizontalHeaderLabels(["Path", "Actions"])
        self.config_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        logging.debug("Initialized config_table")

        # Populate with existing config files
        for config_file in config_files:
            self.add_config_file(config_file)

        layout.addWidget(self.config_table)

        # Add config file button
        add_btn = QPushButton("Add Config File")
        add_btn.setObjectName("add_btn")
        add_btn.clicked.connect(self.add_new_config_file)
        layout.addWidget(add_btn)

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_config_file(self, file_path):
        row = self.config_table.rowCount()
        self.config_table.insertRow(row)
        logging.debug("Added row to config_table")

        # Path
        path_item = QTableWidgetItem(file_path)
        path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
        self.config_table.setItem(row, 0, path_item)

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_config_file(row))
        self.config_table.setCellWidget(row, 1, remove_btn)

    def add_new_config_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Config File")
        file_dialog.setNameFilter("Config Files (*.xglc);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)

        if file_dialog.exec() == QDialog.Accepted:
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.add_config_file(selected_files[0])

    def remove_config_file(self, row):
        self.config_table.removeRow(row)

    def get_config_files(self):
        config_files = []
        for row in range(self.config_table.rowCount()):
            config_files.append(self.config_table.item(row, 0).text())
        return config_files
