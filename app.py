#!/usr/bin/env python3

import glob
import logging
import sys
import webbrowser

from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from logger import log_level_pretty
from app_misc import create_default_settings, validate_settings
from app_editdata import MissingSpeakerDialog
from app_processmanager import ProcessManager
from app_processthread import ProcessThread
from app_settings import SettingsDialog
from app_db import SpeakerDatabase


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GLL2TXT Converter")
        self.resize(1000, 700)
        self.settings = create_default_settings()

        # Initialize database
        self.speaker_db = SpeakerDatabase()
        self.speaker_db.log_signal.connect(self.log_message)

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
        self.log_area.setAcceptRichText(True)
        self.log_area.setDocumentTitle("Logs")
        main_layout.addWidget(self.log_area)

        # Process button and progress area
        bottom_layout = QHBoxLayout()

        self.process_button = QPushButton("Process GLL Files")
        self.process_button.clicked.connect(self.start_processing)
        bottom_layout.addWidget(self.process_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        bottom_layout.addWidget(self.progress_bar)

        # Exit button
        self.exit_button = QPushButton("Exit")
        self.exit_button.setVisible(True)
        self.exit_button.clicked.connect(self.close)
        bottom_layout.addWidget(self.exit_button)

        main_layout.addLayout(bottom_layout)

        # Process manager setup
        self.process_manager = ProcessManager(self.settings)
        self.process_thread = None

        # Connect signals
        self.process_manager.log_signal.connect(self.log_message)
        self.process_manager.progress_signal.connect(self.update_progress)
        self.process_manager.process_complete_signal.connect(self.processing_complete)
        self.process_manager.speaker_data_required_signal.connect(
            self.request_speaker_data
        )

        self.display_initial_informations()

    def display_initial_informations(self):
        oks, errors = validate_settings(self.settings)
        for msg in oks:
            self.log_message(logging.INFO, msg)
        for msg in errors:
            self.log_message(logging.ERROR, msg)

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        # Settings Action
        settings_action = file_menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)

        # Manage Speakers Action
        manage_speakers_action = file_menu.addAction("Edit speakers data")
        manage_speakers_action.triggered.connect(self.open_speaker_management)

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

    def open_speaker_management(self):
        """Open dialog to manage speakers"""
        # Get all GLL files from the current settings
        gll_directory = self.settings.value("gll_files_directory")

        if not gll_directory:
            QMessageBox.warning(
                self,
                "No Directory",
                "Please set the GLL files directory in Settings first.",
            )
            return

        # Ensure Windows-style paths
        gll_directory = gll_directory.replace("/", "\\")
        pattern = f"{gll_directory}\\**\\*.GLL"
        gll_files = list(glob.iglob(pattern, recursive=True))

        # Open MissingSpeakerDialog with all GLL files
        speaker_dialog = MissingSpeakerDialog(gll_files, self.settings, self)
        speaker_dialog.exec()

    def open_github(self):
        webbrowser.open("https://github.com/pierreaubert/gll2txt")

    def open_settings(self):
        """Open settings dialog"""
        settings_dialog = SettingsDialog(self.settings, self)
        settings_dialog.finished.connect(self.display_initial_informations)
        settings_dialog.exec()

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "About GLL2TXT Converter",
            "GLL2TXT Converter\n\nConverts GLL files using Ease binary\nVersion 1.0.0\nLicense: GPL v2.0\nCopyright 2025 @pierreaubert",
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
            self.log_message(logging.INFO, "Processing completed successfully.")
        else:
            self.log_message(
                logging.WARNING, "Processing failed. Check settings and logs!"
            )

    def log_message(self, level, message):
        """Add a colored log message to the log area"""
        # Define colors for different log levels
        colors = {
            logging.DEBUG: "#808080",  # Gray
            logging.INFO: "#014421",  # Green
            logging.WARNING: "#FFA500",  # Orange
            logging.ERROR: "#FF0000",  # Red
            logging.CRITICAL: "#8B0000",  # Dark Red
        }

        # Get the color for this level
        color = colors.get(level, "#000000")

        # Create HTML formatted text with color
        level_txt = log_level_pretty(level)
        formatted_text = f'<span style="color: {color};">{level_txt} {message}</span>'

        # Append the text to the log area
        previous = self.log_area.toHtml()
        self.log_area.setHtml(previous + formatted_text)

        # Scroll to the bottom
        self.log_area.verticalScrollBar().setValue(
            self.log_area.verticalScrollBar().maximum()
        )

    def update_progress(self, value):
        self.progress_bar.setValue(value)

        # Show exit button when progress reaches 100%
        if value == 100:
            self.process_button.setVisible(False)
            self.exit_button.setVisible(True)
        else:
            self.process_button.setVisible(True)
            self.exit_button.setVisible(False)

    def request_speaker_data(self, input_paths):
        # This is where you would handle the request for speaker data
        # For example, you could open a dialog to input the speaker data
        speaker_dialog = MissingSpeakerDialog(input_paths, self)
        speaker_dialog.exec()

    def open_files(self):
        """Open file dialog to select GLL files"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select GLL Files", "", "GLL Files (*.GLL);;All Files (*)"
        )

        if file_paths:
            # You can implement logic to handle selected files
            # For now, just log the selected files
            for path in file_paths:
                self.log_message(logging.INFO, f"Selected file: {path}")

    def open_settings_dialog(self):
        """Open settings dialog"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.exec()


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
