import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)


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
        # Force Qt dialog instead of native dialog
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Config File",
            "",
            "Config Files (*.xglc);;All Files (*)",
            options=options,
        )
        if file_path:
            self.add_config_file(file_path)

    def remove_config_file(self, row):
        self.config_table.removeRow(row)

    def get_config_files(self):
        config_files = []
        for row in range(self.config_table.rowCount()):
            config_files.append(self.config_table.item(row, 0).text())
        return config_files
