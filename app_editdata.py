import os

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


class MissingSpeakerDialog(QDialog):
    def __init__(self, gll_files, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Speaker Data Management")
        self.resize(1000, 800)
        self.settings = settings

        # Main layout
        main_layout = QVBoxLayout()

        # Speaker Database
        self.speaker_db = SpeakerDatabase()

        # Separate lists for missing and existing speaker data
        self.missing_gll_files = []
        self.existing_speaker_data = []

        # Categorize GLL files
        for gll_file in gll_files:
            speaker_data = self.speaker_db.get_speaker_data(gll_file)
            if not speaker_data:
                self.missing_gll_files.append(gll_file)
            else:
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
            self.missing_table.setColumnCount(4)
            self.missing_table.setHorizontalHeaderLabels(
                ["GLL File", "Speaker Name", "Config Files", "Skip"]
            )
            self.missing_table.horizontalHeader().setSectionResizeMode(
                QHeaderView.Stretch
            )

            self.missing_table.setRowCount(len(self.missing_gll_files))
            self.missing_config_files = [[] for _ in self.missing_gll_files]
            self.missing_skip_states = [False for _ in self.missing_gll_files]

            for row, gll_file in enumerate(self.missing_gll_files):
                # GLL File column
                file_item = QTableWidgetItem(gll_file)
                file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
                self.missing_table.setItem(row, 0, file_item)

                # Speaker Name column
                speaker_input = QLineEdit()
                speaker_input.setObjectName("speaker_input")
                self.missing_table.setCellWidget(row, 1, speaker_input)

                # Config Files column
                config_btn = QPushButton("Add Config Files")
                config_btn.setObjectName("config_btn")
                config_btn.clicked.connect(
                    lambda checked, r=row: self.add_config_files(r, is_missing=True)
                )
                self.missing_table.setCellWidget(row, 2, config_btn)

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
                self.missing_table.setCellWidget(row, 3, skip_cell_widget)

            main_layout.addWidget(self.missing_table)

        # Existing Speaker Section
        existing_label = QLabel("Existing Speaker Information:")
        existing_label.setObjectName("existing_label")
        main_layout.addWidget(existing_label)

        # Existing Speaker Table
        self.existing_table = QTableWidget()
        self.existing_table.setObjectName("existing_table")
        self.existing_table.setColumnCount(5)
        self.existing_table.setHorizontalHeaderLabels(
            ["GLL File", "Speaker Name", "Config Files", "Skip", "Actions"]
        )
        self.existing_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

    def update_existing_table(self):
        """Update existing speaker table"""
        # Set row count
        self.existing_table.setRowCount(len(self.existing_speaker_data))

        # Populate table
        for row, data in enumerate(self.existing_speaker_data):
            # GLL File
            file_item = QTableWidgetItem(data["gll_file"])
            file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
            self.existing_table.setItem(row, 0, file_item)

            # Speaker Name (Editable)
            speaker_input = QLineEdit()
            speaker_input.setText(data["speaker_name"])
            speaker_input.setObjectName("speaker_input")
            self.existing_table.setCellWidget(row, 1, speaker_input)

            # Config Files
            config_btn = QPushButton(f"Config Files ({len(data['config_files'])})")
            config_btn.setObjectName("config_btn")
            config_btn.clicked.connect(
                lambda checked, d=data: self.edit_config_files(d)
            )
            self.existing_table.setCellWidget(row, 2, config_btn)

            # Skip checkbox
            skip_checkbox = QCheckBox()
            skip_checkbox.setChecked(data.get("skip", False))
            skip_checkbox.stateChanged.connect(
                lambda state, d=data: self.on_existing_skip_changed(d, state)
            )
            skip_checkbox.setObjectName("skip_checkbox")
            skip_cell_widget = QWidget()
            skip_layout = QHBoxLayout(skip_cell_widget)
            skip_layout.addWidget(skip_checkbox)
            skip_layout.setAlignment(Qt.AlignCenter)
            skip_layout.setContentsMargins(0, 0, 0, 0)
            self.existing_table.setCellWidget(row, 3, skip_cell_widget)

            # Delete Button
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("delete_btn")
            delete_btn.clicked.connect(lambda checked, d=data: self.delete_speaker(d))
            self.existing_table.setCellWidget(row, 4, delete_btn)

    def add_config_files(self, row, is_missing=False):
        """Open file dialog to select config files"""
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

    def edit_config_files(self, data):
        """Open dialog to edit config files for an existing entry"""
        config_dialog = QDialog(self)
        config_dialog.setWindowTitle("Edit Config Files")
        config_dialog.resize(600, 400)

        layout = QVBoxLayout()

        # Table for config files
        config_table = QTableWidget()
        config_table.setColumnCount(2)
        config_table.setHorizontalHeaderLabels(["Path", "Actions"])
        config_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Populate with existing config files
        config_files = data.get("config_files", [])
        config_table.setRowCount(len(config_files))

        for row, config_file in enumerate(config_files):
            # Path
            path_item = QTableWidgetItem(config_file)
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            config_table.setItem(row, 0, path_item)

            # Remove button
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(
                lambda checked, r=row: self.remove_config_file(config_table, r)
            )
            config_table.setCellWidget(row, 1, remove_btn)

        layout.addWidget(config_table)

        # Add config file button
        add_btn = QPushButton("Add Config File")
        add_btn.clicked.connect(lambda: self.add_new_config_file(config_table))
        layout.addWidget(add_btn)

        # Save and Cancel buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(config_dialog.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(config_dialog.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        config_dialog.setLayout(layout)

        def handle_result():
            if config_dialog.result() == QDialog.Accepted:
                # Update config files
                updated_configs = []
                for row in range(config_table.rowCount()):
                    config_path = config_table.item(row, 0).text()
                    updated_configs.append(config_path)

                # Update in existing speaker data
                data["config_files"] = updated_configs

                # Update button text in existing table
                for row in range(self.existing_table.rowCount()):
                    if self.existing_table.item(row, 0).text() == data["gll_file"]:
                        btn = self.existing_table.cellWidget(row, 2)
                        btn.setText(f"Config Files ({len(updated_configs)})")
                        break

        config_dialog.finished.connect(handle_result)
        config_dialog.open()

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
        """Delete speaker data from database"""
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete speaker data for {data['gll_file']}?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Remove from database
            self.speaker_db.delete_speaker(data["gll_file"])

            # Remove from existing data
            self.existing_speaker_data.remove(data)

            # Refresh table
            self.update_existing_table()

    def on_missing_skip_changed(self, row, state):
        """Handle skip checkbox state change for missing entries"""
        self.missing_skip_states[row] = bool(state)

    def on_existing_skip_changed(self, data, state):
        """Handle skip checkbox state change for existing entries"""
        data["skip"] = bool(state)

    def save_all_changes(self):
        """Save changes for both missing and existing speaker data"""
        # Validate and save missing speaker data
        if hasattr(self, "missing_table"):
            for row in range(self.missing_table.rowCount()):
                # Get speaker name
                speaker_input = self.missing_table.cellWidget(row, 1)
                speaker_name = speaker_input.text().strip()
                gll_file = self.missing_table.item(row, 0).text()

                # Validate speaker name
                if not speaker_name:
                    QMessageBox.warning(
                        self,
                        "Invalid Input",
                        f"Please enter a speaker name for {gll_file}",
                    )
                    return

                # Get config files
                config_files = self.missing_config_files[row]

                # Validate config files
                for config_file in config_files:
                    if not os.path.exists(config_file):
                        QMessageBox.warning(
                            self,
                            "Invalid Config File",
                            f"Config file does not exist: {config_file}",
                        )
                        return

                # Save to database
                self.speaker_db.save_speaker_data(
                    gll_file=gll_file,
                    speaker_name=speaker_name,
                    config_files=config_files,
                    skip=self.missing_skip_states[row],
                )

        # Save changes for existing speaker data
        for row in range(self.existing_table.rowCount()):
            gll_file = self.existing_table.item(row, 0).text()

            # Get speaker name
            speaker_input = self.existing_table.cellWidget(row, 1)
            speaker_name = speaker_input.text().strip()

            # Validate speaker name
            if not speaker_name:
                QMessageBox.warning(
                    self, "Invalid Input", f"Please enter a speaker name for {gll_file}"
                )
                return

            # Find corresponding existing data
            for data in self.existing_speaker_data:
                if data["gll_file"] == gll_file:
                    # Save to database
                    self.speaker_db.save_speaker_data(
                        gll_file,
                        speaker_name,
                        data["config_files"],
                        skip=data.get("skip", False),
                    )
                    break

        # Close dialog
        self.accept()
