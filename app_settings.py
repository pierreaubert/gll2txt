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

from app_misc import get_windows_documents_path, DEFAULT_EASE_PATH, DEFAULT_GLL_PATH


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
        self.ease_path_layout = self.create_file_input_row(
            layout,
            "Path to Ease Binary:",
            self.select_ease_binary,
            DEFAULT_EASE_PATH,
        )

        # GLL Files Path
        self.gll_path_layout = self.create_dir_input_row(
            layout,
            "GLL Files Directory:",
            self.select_gll_directory,
            DEFAULT_GLL_PATH,
        )

        # Output Path
        default_output_path = os.path.join(
            get_windows_documents_path(),
            "GLL2TXT_Output",
        )
        self.output_path_layout = self.create_dir_input_row(
            layout,
            "Output Directory:",
            self.select_output_directory,
            default_output_path,
        )

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        # Load existing settings
        self.ease_path_layout["input"].setText(
            self.settings.value("ease_binary_path", DEFAULT_EASE_PATH)
        )
        self.gll_path_layout["input"].setText(
            self.settings.value("gll_files_directory", DEFAULT_GLL_PATH)
        )
        self.output_path_layout["input"].setText(
            self.settings.value(
                "output_directory",
                os.path.join(
                    get_windows_documents_path(),
                    "GLL2TXT_Output",
                ),
            )
        )

        self.setLayout(layout)

    def create_file_input_row(self, layout, label_text, select_method, default_path=""):
        """
        Create a row with a label, input field, and browse button for file selection.

        Args:
            layout (QVBoxLayout): The layout to which this row is added.
            label_text (str): The text for the label.
            select_method (function): Method to call on browse button click.
            default_path (str, optional): Default path for the input field. Defaults to "".

        Returns:
            dict: Containing the label, input field, and button widgets.
        """
        row_layout = QHBoxLayout()
        label = QLabel(label_text)
        input_field = QLineEdit()
        input_field.setText(default_path)

        # Add color highlighting based on file existence
        self.update_path_highlight(input_field, default_path)

        # Connect textChanged signal to update highlighting
        input_field.textChanged.connect(
            lambda: self.update_path_highlight(input_field, input_field.text())
        )

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(select_method)

        row_layout.addWidget(label)
        row_layout.addWidget(input_field)
        row_layout.addWidget(browse_button)
        layout.addLayout(row_layout)

        return {"label": label, "input": input_field, "button": browse_button}

    def update_path_highlight(self, input_field, path):
        """
        Update input field color based on file/directory existence
        Green if path exists, red if it doesn't
        """
        if not path:
            # No path entered
            input_field.setStyleSheet("QLineEdit { background-color: white; }")
            return

        # Check if path exists
        exists = os.path.exists(path)

        if exists:
            # Path exists - green highlight
            input_field.setStyleSheet(
                "QLineEdit { "
                "background-color: #90EE90; "  # Light green
                "border: 1px solid green; "
                "}"
            )
        else:
            # Path does not exist - red highlight
            input_field.setStyleSheet(
                "QLineEdit { "
                "background-color: #FFB6C1; "  # Light red
                "border: 1px solid red; "
                "}"
            )

    def create_dir_input_row(self, layout, label_text, select_method, default_path=""):
        """
        Create a row for directory input, reusing file input creation logic.

        Args:
            layout (QVBoxLayout): The layout to which this row is added.
            label_text (str): The text for the label.
            select_method (function): Method to call on browse button click.
            default_path (str, optional): Default path for the input field. Defaults to "".

        Returns:
            dict: Containing the label, input field, and button widgets.
        """
        return self.create_file_input_row(
            layout, label_text, select_method, default_path
        )

    def select_ease_binary(self):
        """
        Open file dialog to select Ease binary file and update the input field.
        """
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select Ease Binary")
        file_dialog.setNameFilter("Executable Files (*.exe);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Force Qt dialog

        current_path = self.ease_path_layout["input"].text()
        if current_path:
            file_dialog.setDirectory(os.path.dirname(current_path))

        def handle_selection():
            if file_dialog.result() == QDialog.Accepted:
                selected_files = file_dialog.selectedFiles()
                if selected_files:
                    file_path = selected_files[0]
                    self.ease_path_layout["input"].setText(file_path)

        file_dialog.finished.connect(handle_selection)
        file_dialog.open()

    def select_gll_directory(self):
        """
        Open directory dialog to select GLL files directory and update the input field.
        """
        dir_dialog = QFileDialog(self)
        dir_dialog.setWindowTitle("Select GLL Files Directory")
        dir_dialog.setFileMode(QFileDialog.Directory)
        dir_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dir_dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Force Qt dialog

        current_path = self.gll_path_layout["input"].text()
        if current_path:
            dir_dialog.setDirectory(current_path)

        def handle_selection():
            if dir_dialog.result() == QDialog.Accepted:
                selected_dirs = dir_dialog.selectedFiles()
                if selected_dirs:
                    dir_path = selected_dirs[0]
                    self.gll_path_layout["input"].setText(dir_path)

        dir_dialog.finished.connect(handle_selection)
        dir_dialog.open()

    def select_output_directory(self):
        """
        Open directory dialog to select output directory and update the input field.
        """
        dir_dialog = QFileDialog(self)
        dir_dialog.setWindowTitle("Select Output Directory")
        dir_dialog.setFileMode(QFileDialog.Directory)
        dir_dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dir_dialog.setOption(QFileDialog.DontUseNativeDialog, True)  # Force Qt dialog

        current_path = self.output_path_layout["input"].text()
        if current_path:
            dir_dialog.setDirectory(current_path)

        def handle_selection():
            if dir_dialog.result() == QDialog.Accepted:
                selected_dirs = dir_dialog.selectedFiles()
                if selected_dirs:
                    dir_path = selected_dirs[0]
                    self.output_path_layout["input"].setText(dir_path)

        dir_dialog.finished.connect(handle_selection)
        dir_dialog.open()

    def save_settings(self):
        """
        Save current settings using QSettings for persistent storage.
        """
        # Save paths
        self.settings.setValue(
            "ease_binary_path", self.ease_path_layout["input"].text()
        )
        self.settings.setValue(
            "gll_files_directory", self.gll_path_layout["input"].text()
        )
        self.settings.setValue(
            "output_directory", self.output_path_layout["input"].text()
        )

        self.accept()
