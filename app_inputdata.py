import os

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
    QVBoxLayout,
)

from app_db import SpeakerDatabase


class SpeakerInputDialog(QDialog):
    def __init__(self, gll_file, parent=None):
        super().__init__(parent)
        self.gll_file = gll_file
        self.speaker_db = SpeakerDatabase()

        self.setWindowTitle("Speaker Information")
        self.setModal(True)
        self.resize(500, 300)

        # Main layout
        layout = QVBoxLayout()

        # GLL File Path
        file_layout = QHBoxLayout()
        file_label = QLabel("GLL File:")
        file_path = QLineEdit()
        file_path.setText(gll_file)
        file_path.setReadOnly(True)
        file_layout.addWidget(file_label)
        file_layout.addWidget(file_path)
        layout.addLayout(file_layout)

        # Speaker Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Speaker Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # Config Files Section
        config_label = QLabel("Config Files:")
        layout.addWidget(config_label)

        # Config Files Table
        self.config_table = QTableWidget(0, 2)
        self.config_table.setHorizontalHeaderLabels(["Path", "Actions"])
        self.config_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        layout.addWidget(self.config_table)

        # Add Config File Button
        add_config_btn = QPushButton("Add Config File")
        add_config_btn.clicked.connect(self.add_config_file)
        layout.addWidget(add_config_btn)

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_speaker_data)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def add_config_file(self):
        """Add a new config file row to the table"""
        row = self.config_table.rowCount()
        self.config_table.insertRow(row)

        # Path input
        path_input = QLineEdit()
        self.config_table.setCellWidget(row, 0, path_input)

        # Browse button
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(lambda: self.browse_config_file(path_input))
        self.config_table.setCellWidget(row, 1, browse_btn)

    def browse_config_file(self, path_input):
        """Open file dialog to select config file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Config File", "", "Config Files (*.cfg *.ini);;All Files (*)"
        )
        if file_path:
            path_input.setText(file_path)

    def save_speaker_data(self):
        """Validate and save speaker data"""
        # Validate speaker name
        speaker_name = self.name_input.text().strip()
        if not speaker_name:
            QMessageBox.warning(self, "Invalid Input", "Speaker name cannot be empty.")
            return

        # Collect config files
        config_files = []
        for row in range(self.config_table.rowCount()):
            path_input = self.config_table.cellWidget(row, 0)
            config_file = path_input.text().strip()

            if config_file:
                # Validate config file exists
                if not os.path.exists(config_file):
                    QMessageBox.warning(
                        self,
                        "Invalid Config File",
                        f"Config file does not exist: {config_file}",
                    )
                    return
                config_files.append(config_file)

        # Save to database
        try:
            self.speaker_db.save_speaker_data(
                gll_file=self.gll_file,
                speaker_name=speaker_name,
                config_files=config_files,
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save speaker data: {str(e)}"
            )
