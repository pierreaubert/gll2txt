#!/usr/bin/env python3

import logging
import sys
import traceback
import webbrowser
from pathlib import Path

from qt_init import init_qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app_editdata import EditSpeakerDialog
from app_misc import create_default_settings, validate_settings
from app_processmanager import ProcessManager
from app_processthread import ProcessThread
from app_settings import SettingsDialog
from database import SpeakerDatabase
from logger import log_level_pretty


class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            logging.info("Initializing main window")

            # Initialize instance variables
            self.process_thread = None
            self.process_manager = None
            self.speaker_db = None
            self.settings = None
            self.log_area = None
            self.progress_bar = None
            self.process_button = None
            self.exit_button = None
            self.manage_speakers_button = None
            self.log_filter_buttons = {}
            self.stored_messages = []  # Store all log messages

            self.setWindowTitle("GLL2TXT Converter")
            self.resize(1000, 700)

            logging.debug("Loading settings")
            try:
                self.settings = create_default_settings()
            except Exception as e:
                logging.error("Failed to load settings", exc_info=True)
                raise RuntimeError("Failed to load application settings") from e

            # Initialize database
            logging.debug("Initializing database")
            try:
                speaker_db_dir = Path.home() / "Documents"
                speaker_db_dir.mkdir(parents=True, exist_ok=True)
                speaker_db_file = speaker_db_dir / "GLL2TXT_Speakers.db"
                self.speaker_db = SpeakerDatabase(speaker_db_file)
                self.speaker_db.log_signal.connect(self.log_message)
            except Exception as e:
                logging.error(
                    "Failed to initialize database: %s", str(e), exc_info=True
                )
                raise RuntimeError("Failed to initialize database") from e

            # Central widget and main layout
            logging.debug("Setting up UI layout")
            try:
                central_widget = QWidget()
                main_layout = QVBoxLayout()
                central_widget.setLayout(main_layout)
                self.setCentralWidget(central_widget)

                # Create menu bar
                self.create_menu_bar()

                # Log filter controls
                log_filter_layout = QHBoxLayout()
                log_filter_label = QLabel("Log Level Filter:")
                log_filter_layout.addWidget(log_filter_label)

                for level in [
                    logging.DEBUG,
                    logging.INFO,
                    logging.WARNING,
                    logging.ERROR,
                ]:
                    btn = QPushButton(log_level_pretty(level))
                    btn.setCheckable(True)
                    btn.setChecked(True)  # All levels shown by default
                    btn.clicked.connect(
                        lambda checked, lvl=level: self.update_log_filter(lvl, checked)
                    )
                    log_filter_layout.addWidget(btn)
                    self.log_filter_buttons[level] = btn

                main_layout.addLayout(log_filter_layout)

                # Log area
                self.log_area = QTextEdit()
                self.log_area.setReadOnly(True)
                self.log_area.setAcceptRichText(True)
                self.log_area.setDocumentTitle("Logs")
                main_layout.addWidget(self.log_area)

                # Process manager setup
                self.process_manager = ProcessManager(self.settings, self.speaker_db)
                self.process_thread = None

                # Process button and progress area
                bottom_layout = QHBoxLayout()

                # Add speaker management button
                self.manage_speakers_button = QPushButton("Edit speakers data")
                self.manage_speakers_button.clicked.connect(
                    self.open_speaker_management
                )
                bottom_layout.addWidget(self.manage_speakers_button)

                self.process_button = QPushButton("Process GLL Files")
                self.process_button.clicked.connect(self.start_processing)
                self.process_button.setVisible(True)
                bottom_layout.addWidget(self.process_button)

                self.progress_bar = QProgressBar()
                self.progress_bar.setVisible(False)
                bottom_layout.addWidget(self.progress_bar)

                # Stop button
                self.stop_button = QPushButton("Stop")
                self.stop_button.setVisible(True)
                self.stop_button.clicked.connect(self.process_manager.stop_processing)
                bottom_layout.addWidget(self.stop_button)

                # Exit button
                self.exit_button = QPushButton("Exit")
                self.exit_button.setVisible(True)
                self.exit_button.clicked.connect(self.close)
                bottom_layout.addWidget(self.exit_button)

                main_layout.addLayout(bottom_layout)

                # Connect signals
                self.process_manager.log_signal.connect(self.log_message)
                self.process_manager.progress_signal.connect(self.update_progress)
                self.process_manager.speaker_data_required_signal.connect(
                    self.open_speaker_management
                )

                # Display initial information
                logging.debug("Displaying initial information")
                try:
                    self.display_initial_informations()
                except Exception as e:
                    logging.error(
                        "Failed to display initial information", exc_info=True
                    )
                    # Non-critical error, just log it
                    self.log_message(
                        logging.ERROR,
                        f"Failed to display initial information: {str(e)}",
                    )

                logging.info("Main window initialization complete")

            except Exception as e:
                logging.error("Failed to initialize UI", exc_info=True)
                raise RuntimeError("Failed to initialize user interface") from e

        except Exception:
            logging.error("Failed to initialize main window", exc_info=True)
            raise

    def stop_processing(self):
        self.stop_process = True

    def closeEvent(self, event):
        """Handle window close event"""
        try:
            logging.info("Application shutting down")

            # Stop any running process
            if self.process_thread and self.process_thread.isRunning():
                logging.debug("Stopping process thread")
                self.process_thread.quit()
                self.process_thread.wait()

            # Clean up database
            if self.speaker_db:
                logging.debug("Disconnecting database signals")
                try:
                    self.speaker_db.log_signal.disconnect()
                except TypeError:
                    pass  # Signal might not be connected
                logging.debug("Cleaning up database")
                self.speaker_db.cleanup()
                self.speaker_db = None

            logging.info("Cleanup complete")
            event.accept()

        except Exception:
            logging.error("Error during shutdown", exc_info=True)
            event.ignore()

    def display_initial_informations(self):
        is_valid, errors = validate_settings(self.settings)
        if is_valid:
            self.log_message(logging.INFO, "Settings validation successful")
        for msg in errors:
            self.log_message(logging.ERROR, msg)

    def create_menu_bar(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        # Settings Action
        settings_action = file_menu.addAction("&Settings")
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.open_settings)

        # Manage Speakers Action
        manage_speakers_action = file_menu.addAction("&Edit speakers data")
        manage_speakers_action.setShortcut("Ctrl+E")
        manage_speakers_action.triggered.connect(self.open_speaker_management)

        # Process Files Action
        process_files_action = file_menu.addAction("&Process Files")
        process_files_action.setShortcut("Ctrl+P")
        process_files_action.triggered.connect(self.start_processing)

        file_menu.addSeparator()

        # Exit Action
        exit_action = file_menu.addAction("E&xit")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")

        # GitHub Link
        github_action = help_menu.addAction("&GitHub Repository")
        github_action.setShortcut("F1")
        github_action.triggered.connect(self.open_github)

        # About Action
        about_action = help_menu.addAction("&About")
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

        # Convert to Path object for cross-platform compatibility
        gll_path = Path(gll_directory)
        if not gll_path.exists():
            QMessageBox.warning(
                self,
                "Invalid Directory",
                f"Directory does not exist: {gll_directory}",
            )
            return

        # Search for both .GLL and .gll files using pathlib
        gll_files = []
        for ext in [".GLL", ".gll"]:
            # Use rglob but filter out directories that start or end with __
            for file in gll_path.rglob(f"*{ext}"):
                # Check each directory in the path
                skip_file = False
                for part in file.parts:
                    if part.startswith("__") or part.endswith("__"):
                        skip_file = True
                        break
                if not skip_file:
                    gll_files.append(file)

        # Convert Path objects to strings and remove duplicates
        gll_files = [str(f) for f in gll_files]
        gll_files = list(set(gll_files))

        if not gll_files:
            QMessageBox.warning(
                self,
                "No GLL Files",
                f"No GLL files found in directory: {gll_directory}",
            )
            return

        # Open MissingSpeakerDialog with all GLL files
        speaker_dialog = EditSpeakerDialog(
            settings=self.settings,
            gll_files=gll_files,
            parent=self,
            test_mode=False,
            speaker_db=self.speaker_db,
        )
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
        # show progress bar
        self.progress_bar.setVisible(True)

        # Reset progress bar
        self.progress_bar.setValue(0)

        # Clear log area
        self.log_area.clear()

        # Create and start processing thread
        self.process_thread = ProcessThread(self.process_manager)
        self.process_thread.log_signal.connect(self.log_message)
        self.process_thread.progress_signal.connect(self.update_progress)

        self.process_thread.start()

    def log_message(self, level, message):
        """Log a message to the log area with color based on level"""
        try:
            color = {
                logging.DEBUG: "gray",
                logging.INFO: "black",
                logging.WARNING: "orange",
                logging.ERROR: "red",
                logging.CRITICAL: "darkred",
            }.get(level, "black")

            formatted_message = f'<font color="{color}">[{log_level_pretty(level)}] {message}</font><br>'

            # Store the message with its level
            self.stored_messages.append((level, formatted_message))

            # Only display if it meets the current filter
            if self.should_show_log_level(level):
                self.log_area.moveCursor(QTextCursor.End)
                self.log_area.insertHtml(formatted_message)

                # Scroll to bottom
                scrollbar = self.log_area.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            print(f"Error logging message: {str(e)}")
            traceback.print_exc()

    def should_show_log_level(self, level):
        """Determine if a log message at the given level should be shown based on filter settings"""
        # Find the lowest checked level
        lowest_checked = None
        for check_level in [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
        ]:
            if (
                check_level in self.log_filter_buttons
                and self.log_filter_buttons[check_level].isChecked()
            ):
                lowest_checked = check_level
                break

        # If we found a checked level, only show messages at or above that level
        if lowest_checked is not None:
            return level >= lowest_checked

        # If no level is checked, show everything
        return True

    def update_log_filter(self, level, checked):
        """Update log filter when a button is toggled"""
        try:
            # Don't allow unchecking if it's the only checked button
            if not checked and not any(
                btn.isChecked()
                for btn in self.log_filter_buttons.values()
                if btn != self.log_filter_buttons[level]
            ):
                self.log_filter_buttons[level].setChecked(True)
                return

            # Refresh the display from stored messages
            self.refresh_log_view()

        except Exception as e:
            print(f"Error updating log filter: {str(e)}")
            traceback.print_exc()

    def refresh_log_view(self):
        """Refresh the log view based on current filter settings"""
        try:
            self.log_area.clear()

            # Re-display all stored messages that match the current filter
            for level, message in self.stored_messages:
                if self.should_show_log_level(level):
                    self.log_area.moveCursor(QTextCursor.End)
                    self.log_area.insertHtml(message)

            # Scroll to bottom
            scrollbar = self.log_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

        except Exception as e:
            print(f"Error refreshing log view: {str(e)}")
            traceback.print_exc()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def open_files(self):
        """Open file dialog to select GLL files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select GLL Files", "", "GLL Files (*.GLL *.gll);;All Files (*)"
        )
        if files:
            self.gll_files = files
            self.log_message(logging.INFO, f"Selected {len(files)} files")


def main():
    try:
        # Initialize Qt before creating QApplication
        init_qt()
        app = QApplication(sys.argv)

        # Configure logging
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("gll2txt.log"), logging.StreamHandler()],
        )
        logging.info("Starting GLL2TXT application")

        # Set up global exception handler for Qt
        def handle_exception(exc_type, exc_value, exc_traceback):
            logging.error(
                "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
            )
            # Show error dialog to user
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Critical)
            error_msg.setText("An unexpected error occurred")
            error_msg.setInformativeText(str(exc_value))
            error_msg.setDetailedText(
                "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            )
            error_msg.setWindowTitle("Error")
            error_msg.exec()

        sys.excepthook = handle_exception

        try:
            main_window = MainWindow()
            main_window.show()
            logging.info("Main window initialized and shown")
        except Exception:
            logging.error("Failed to initialize main window", exc_info=True)
            raise

        return app.exec()
    except Exception:
        logging.error("Fatal error in main", exc_info=True)
        raise


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        logging.error("Application crashed", exc_info=True)
        sys.exit(1)
