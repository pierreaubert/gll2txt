import os

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app_misc import get_windows_documents_path, DEFAULT_EASE_PATH


class SettingsDialog(QDialog):
    """
    Dialog for configuring application settings related to file paths.
    Provides input fields for setting paths to Ease binary, GLL files directory,
    and output directory. Paths are validated for existence and settings are
    saved persistently.
    """

    def __init__(self, settings, parent=None):
        """
        Initialize the dialog, create UI elements, and load existing settings.

        Args:
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.resize(600, 300)
        self.settings = settings

        # Layout
        layout = QVBoxLayout()

        # Ease Binary Path
        ease_binary_label = QLabel("Path to Ease Binary:")
        ease_binary_label.setObjectName("ease_binary_label")
        ease_binary_input = QLineEdit()
        ease_binary_input.setObjectName("ease_binary")
        ease_binary_input.setText(
            self.settings.value("ease_binary_path", DEFAULT_EASE_PATH)
        )
        ease_binary_browse = QPushButton("Browse...")
        ease_binary_browse.setObjectName("browse_ease")
        ease_binary_browse.clicked.connect(
            lambda: self.browse_file("ease_binary_path", ease_binary_input)
        )

        ease_binary_layout = QHBoxLayout()
        ease_binary_layout.addWidget(ease_binary_label)
        ease_binary_layout.addWidget(ease_binary_input)
        ease_binary_layout.addWidget(ease_binary_browse)
        layout.addLayout(ease_binary_layout)

        # GLL Files Directory
        gll_dir_label = QLabel("GLL Files Directory:")
        gll_dir_label.setObjectName("gll_directory_label")
        gll_dir_input = QLineEdit()
        gll_dir_input.setObjectName("gll_directory")
        gll_dir_input.setText(self.settings.value("gll_files_directory"))
        gll_dir_browse = QPushButton("Browse...")
        gll_dir_browse.setObjectName("browse_gll")
        gll_dir_browse.clicked.connect(
            lambda: self.browse_directory("gll_files_directory", gll_dir_input)
        )

        gll_dir_layout = QHBoxLayout()
        gll_dir_layout.addWidget(gll_dir_label)
        gll_dir_layout.addWidget(gll_dir_input)
        gll_dir_layout.addWidget(gll_dir_browse)
        layout.addLayout(gll_dir_layout)

        # Output Path
        output_dir_label = QLabel("Output Directory:")
        output_dir_label.setObjectName("output_directory_label")
        output_dir_input = QLineEdit()
        output_dir_input.setObjectName("output_directory")
        default_output_path = os.path.join(
            get_windows_documents_path(),
            "GLL2TXT_Output",
        )
        output_dir_input.setText(
            self.settings.value(
                "output_directory",
                default_output_path,
            )
        )
        output_dir_browse = QPushButton("Browse...")
        output_dir_browse.setObjectName("browse_output")
        output_dir_browse.clicked.connect(
            lambda: self.browse_directory("output_directory", output_dir_input)
        )

        output_dir_layout = QHBoxLayout()
        output_dir_layout.addWidget(output_dir_label)
        output_dir_layout.addWidget(output_dir_input)
        output_dir_layout.addWidget(output_dir_browse)
        layout.addLayout(output_dir_layout)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setObjectName("save_button")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancel_button")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def browse_file(self, setting_name, input_field):
        """
        Open file dialog to select file and update the input field.
        """
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select File")
        file_dialog.setNameFilter("All Files (*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Force Qt dialog

        current_path = input_field.text()
        if current_path:
            file_dialog.setDirectory(os.path.dirname(current_path))

        def handle_selection():
            if file_dialog.result() == QDialog.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    input_field.setText(file_path)

        file_dialog.finished.connect(handle_selection)
        file_dialog.open()

    def browse_directory(self, setting_name, input_field):
        """
        Open directory dialog to select directory and update the input field.
        """
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Directory",
            input_field.text() or "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontUseNativeDialog,
        )
        if selected_dir:
            input_field.setText(selected_dir)

    def save_settings(self):
        """
        Save current settings using QSettings for persistent storage.
        """
        # Save paths
        ease_binary = self.findChild(QLineEdit, "ease_binary")
        if ease_binary:
            self.settings.setValue("ease_binary_path", ease_binary.text())

        gll_directory = self.findChild(QLineEdit, "gll_directory")
        if gll_directory:
            self.settings.setValue("gll_files_directory", gll_directory.text())

        output_directory = self.findChild(QLineEdit, "output_directory")
        if output_directory:
            self.settings.setValue("output_directory", output_directory.text())

        self.settings.sync()  # Force sync to ensure settings are saved
        self.accept()
