import glob
import os
import sys
import webbrowser
import winreg
import sqlite3

from PySide6.QtCore import QObject, QThread, QSettings, Signal
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QProgressBar,
    QWidget,
    QApplication,
    QMessageBox,
    QPushButton,
    QDialog,
    QLabel,
    QLineEdit,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QGridLayout,
    QScrollArea,
)
from PySide6.QtGui import QIcon, QAction

from gll2txt import extract_speaker as gll_extract_speaker


def get_windows_documents_path():
    """
    Retrieve the user's Documents folder path on Windows
    """
    try:
        # Open the key for the current user's shell folders
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )

        # Retrieve the path to the personal (Documents) folder
        documents_path = winreg.QueryValueEx(key, "Personal")[0]

        winreg.CloseKey(key)
        return documents_path
    except Exception:
        # Fallback to a default path if retrieval fails
        return os.path.join(os.path.expanduser("~"), "Documents")


class SettingsDialog(QDialog):
    DEFAULT_EASE_PATH = r"C:\Program Files (x86)\AFMG\EASE GLLViewer\EASE GLLViewer.exe"
    DEFAULT_GLL_PATH = r"Z:\GLL"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.resize(600, 300)

        # Layout
        layout = QVBoxLayout()

        # Ease Binary Path
        self.ease_path_layout = self.create_file_input_row(
            layout,
            "Path to Ease Binary:",
            self.select_ease_binary,
            self.DEFAULT_EASE_PATH,
        )

        # GLL Files Path
        self.gll_path_layout = self.create_dir_input_row(
            layout,
            "GLL Files Directory:",
            self.select_gll_directory,
            self.DEFAULT_GLL_PATH,
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

        self.setLayout(layout)

        # Load existing settings
        self.load_settings()

    def create_file_input_row(self, layout, label_text, select_method, default_path=""):
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
        return self.create_file_input_row(
            layout, label_text, select_method, default_path
        )

    def select_ease_binary(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Ease Binary", "", "Executable Files (*.exe);;All Files (*)"
        )
        if file_path:
            self.ease_path_layout["input"].setText(file_path)

    def select_gll_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select GLL Files Directory")
        if dir_path:
            self.gll_path_layout["input"].setText(dir_path)

    def select_output_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_path_layout["input"].setText(dir_path)

    def save_settings(self):
        # Use QSettings for persistent storage
        settings = QSettings("YourCompany", "GLL2TXT")

        # Save paths
        settings.setValue("ease_binary_path", self.ease_path_layout["input"].text())
        settings.setValue("gll_files_directory", self.gll_path_layout["input"].text())
        settings.setValue("output_directory", self.output_path_layout["input"].text())

        self.accept()

    def load_settings(self):
        # Load existing settings
        settings = QSettings("YourCompany", "GLL2TXT")

        # Populate input fields with saved settings or defaults
        self.ease_path_layout["input"].setText(
            settings.value("ease_binary_path", self.DEFAULT_EASE_PATH)
        )
        self.gll_path_layout["input"].setText(
            settings.value("gll_files_directory", self.DEFAULT_GLL_PATH)
        )
        self.output_path_layout["input"].setText(
            settings.value(
                "output_directory",
                os.path.join(
                    get_windows_documents_path(),
                    "GLL2TXT_Output",
                ),
            )
        )


class SpeakerDatabase:
    def __init__(self, db_path=None):
        """
        Initialize SQLite database for speaker data

        Args:
            db_path (str, optional): Path to SQLite database.
                                     Defaults to a file in user's documents folder.
        """
        if db_path is None:
            db_path = os.path.join(get_windows_documents_path(), "GLL2TXT_Speakers.db")

        self.db_path = db_path
        self._create_tables()

    def _create_tables(self):
        """Create necessary tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS speakers (
                    gll_file TEXT PRIMARY KEY,
                    speaker_name TEXT,
                    config_files TEXT
                )
            """)
            conn.commit()

    def save_speaker_data(self, gll_file, speaker_name, config_files):
        """
        Save or update speaker data for a specific GLL file

        Args:
            gll_file (str): Path to the GLL file
            speaker_name (str): Name of the speaker
            config_files (list): List of config file paths
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO speakers 
                (gll_file, speaker_name, config_files) 
                VALUES (?, ?, ?)
            """,
                (gll_file, speaker_name, ";".join(config_files)),
            )
            conn.commit()

    def get_speaker_data(self, gll_file):
        """
        Retrieve speaker data for a specific GLL file

        Args:
            gll_file (str): Path to the GLL file

        Returns:
            dict: Speaker data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT speaker_name, config_files FROM speakers WHERE gll_file = ?",
                (gll_file,),
            )
            result = cursor.fetchone()

            if result:
                return {
                    "speaker_name": result[0],
                    "config_files": result[1].split(";") if result[1] else [],
                }
            return None

    def list_all_speakers(self):
        """
        List all speakers in the database

        Returns:
            list: List of dictionaries containing speaker data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT gll_file, speaker_name, config_files FROM speakers")
            results = cursor.fetchall()

            return [
                {
                    "gll_file": row[0],
                    "speaker_name": row[1],
                    "config_files": row[2].split(";") if row[2] else [],
                }
                for row in results
            ]

    def delete_speaker(self, gll_file):
        """
        Delete speaker data for a specific GLL file

        Args:
            gll_file (str): Path to the GLL file
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM speakers WHERE gll_file = ?", (gll_file,))
            conn.commit()


class ProcessManager(QObject):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    process_complete_signal = Signal(bool)
    speaker_data_required_signal = Signal(str)  # Signal to request speaker data

    def __init__(self):
        super().__init__()
        self.settings = QSettings("spinorama.org", "GLL2TXT")
        self.speaker_db = SpeakerDatabase()

    def get_settings(self):
        return {
            "ease_binary_path": self.settings.value(
                "ease_binary_path",
                r"C:\Program Files (x86)\AFMG\EASE GLLViewer\EASE GLLViewer.exe",
            ),
            "gll_files_directory": self.settings.value(
                "gll_files_directory", r"Z:\GLL"
            ),
            "output_directory": self.settings.value(
                "output_directory",
                os.path.join(
                    get_windows_documents_path(),
                    "GLL2TXT_Output",
                ),
            ),
        }

    def validate_settings(self, settings):
        """Validate that all required settings are present and valid."""
        errors = []

        if not settings["ease_binary_path"]:
            errors.append("Ease binary path is not set")
        elif not os.path.exists(settings["ease_binary_path"]):
            errors.append(f"Ease binary not found: {settings['ease_binary_path']}")

        if not settings["gll_files_directory"]:
            errors.append("GLL files directory is not set")
        elif not os.path.isdir(settings["gll_files_directory"]):
            errors.append(
                f"Invalid GLL files directory: {settings['gll_files_directory']}"
            )

        if not settings["output_directory"]:
            errors.append("Output directory is not set")
        elif not os.path.isdir(settings["output_directory"]):
            os.makedirs(settings["output_directory"], exist_ok=True)

        return errors

    def process_gll_files(self):
        """Process GLL files using Ease binary."""
        settings = self.get_settings()

        # Validate settings first
        validation_errors = self.validate_settings(settings)
        if validation_errors:
            for error in validation_errors:
                self.log_signal.emit(f"Error: {error}")
            self.process_complete_signal.emit(False)
            return

        # List all GLL files
        self.log_signal.emit(f"Searching GLL files {settings['gll_files_directory']}")
        gll_files = list(
            glob.iglob(settings["gll_files_directory"] + "\\**\\*.GLL", recursive=True)
        )

        total_files = len(gll_files)

        if total_files == 0:
            self.log_signal.emit("No GLL files found in the specified directory.")
            self.process_complete_signal.emit(False)
            return

        self.log_signal.emit(f"Found {total_files} GLL files.")

        # Process each GLL file
        self.log_signal.emit(
            f"Processing {total_files} GLL files, output will be saved to {settings['output_directory']}."
        )
        for index, gll_file in enumerate(gll_files, 1):
            input_path = gll_file

            # Try to get speaker data from database
            speaker_data = self.speaker_db.get_speaker_data(input_path)

            if not speaker_data:
                # If no speaker data, request it
                self.speaker_data_required_signal.emit(input_path)
                # Wait for user to provide data (this would be handled in the main window)
                continue

            speaker_name = speaker_data["speaker_name"]
            config_files = speaker_data["config_files"]

            try:
                # Call the imported extract_speaker function
                self.log_signal.emit(f"Processing: {speaker_name} / {gll_file}")
                gll_extract_speaker(
                    output_dir=settings["output_directory"],
                    speaker_name=speaker_name,
                    gll_file=input_path,
                    config_file=config_files[0] if config_files else None,
                )

                self.log_signal.emit(f"Processed: {gll_file}")

                # Update progress
                progress = int((index / total_files) * 100)
                self.progress_signal.emit(progress)

            except Exception as e:
                self.log_signal.emit(
                    f"Unexpected error processing {gll_file}: {str(e)}"
                )

        self.log_signal.emit("Batch processing complete.")
        self.progress_signal.emit(100)
        self.process_complete_signal.emit(True)


class ProcessThread(QThread):
    log_signal = Signal(str)
    progress_signal = Signal(int)
    process_complete_signal = Signal(bool)

    def __init__(self, process_manager):
        super().__init__()
        self.process_manager = process_manager

        # Disconnect any existing connections to prevent duplicate calls
        try:
            self.process_manager.log_signal.disconnect()
            self.process_manager.progress_signal.disconnect()
            self.process_manager.process_complete_signal.disconnect()
        except TypeError:
            # Ignore if no connections exist
            pass

        # Connect signals from process manager
        self.process_manager.log_signal.connect(self.log_signal.emit)
        self.process_manager.progress_signal.connect(self.progress_signal.emit)
        self.process_manager.process_complete_signal.connect(
            self.process_complete_signal.emit
        )

    def run(self):
        self.process_manager.process_gll_files()


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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLL2TXT Converter")
        self.resize(1000, 700)

        # Central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create menu bar
        self.create_menu_bar()

        # Log area
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        main_layout.addWidget(self.log_area)

        # Process button and progress area
        bottom_layout = QHBoxLayout()

        self.process_button = QPushButton("Process GLL Files")
        self.process_button.clicked.connect(self.start_processing)
        bottom_layout.addWidget(self.process_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        main_layout.addLayout(bottom_layout)

        # Process manager setup
        self.process_manager = ProcessManager()
        self.process_thread = None

        # Connect signals
        self.process_manager.log_signal.connect(self.log_message)
        self.process_manager.progress_signal.connect(self.update_progress)
        self.process_manager.speaker_data_required_signal.connect(
            self.request_speaker_data
        )

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        # Settings Action
        settings_action = file_menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)

        # Exit Action
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.close)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")

        # GitHub Link
        github_action = help_menu.addAction("GitHub Repository")
        github_action.triggered.connect(self.open_github)

        # About Action
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_dialog)

    def open_github(self):
        webbrowser.open("https://github.com/pierreaubert/gll2txt")

    def open_settings(self):
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About GLL2TXT Converter",
            "GLL2TXT Converter\n\nConverts GLL files using Ease binary\nVersion 1.0.0",
            "License: GPL v2.0",
            "Copyright 2025 @pierreaubert",
        )

    def start_processing(self):
        # Disable process button
        self.process_button.setEnabled(False)

        # Hide process button, show progress bar
        self.process_button.setVisible(False)
        self.progress_bar.setVisible(True)

        # Reset progress bar
        self.progress_bar.setValue(0)

        # Clear log area
        self.log_area.clear()

        # Create and start processing thread
        self.process_thread = ProcessThread(self.process_manager)
        self.process_thread.log_signal.connect(self.log_message)
        self.process_thread.progress_signal.connect(self.update_progress)
        self.process_thread.process_complete_signal.connect(self.processing_complete)

        self.process_thread.start()

    def processing_complete(self, success):
        # Re-enable process button
        self.process_button.setEnabled(True)

        # Hide progress bar, show process button
        self.progress_bar.setVisible(False)
        self.process_button.setVisible(True)

        # Optional: Show completion message
        if success:
            self.log_message("Processing completed successfully.")
        else:
            self.log_message("Processing failed. Check settings and logs.")

    def log_message(self, message):
        self.log_area.append(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def request_speaker_data(self, input_path):
        # This is where you would handle the request for speaker data
        # For example, you could open a dialog to input the speaker data
        speaker_dialog = SpeakerInputDialog(input_path, self)
        speaker_dialog.exec()


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
