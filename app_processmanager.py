import logging
from pathlib import Path
import os
from PySide6.QtCore import QObject, Signal

from gll2txt import extract_speaker as gll_extract_speaker
from logger import set_global_logger


class ProcessManager(QObject):
    log_signal = Signal(int, str)  # Changed to support level and message
    progress_signal = Signal(int)
    process_complete_signal = Signal(bool)
    speaker_data_required_signal = Signal(list)  # Signal to request speaker data

    def __init__(self, settings, speaker_db):
        super().__init__()
        self.settings = settings
        self.speaker_db = speaker_db
        self.stop_process = False
        # connect the global logger
        set_global_logger(self.log_message)

    def log_message(self, level, message):
        """Helper method to emit log messages with level"""
        self.log_signal.emit(level, message)

    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, "speaker_db"):
            self.speaker_db = None

    def process_gll_files(self):
        """Process GLL files using Ease binary."""
        # List all GLL files
        gll_directory = self.settings.value("gll_files_directory", "")
        if not gll_directory:
            self.log_message(
                logging.ERROR,
                "GLL files directory not set in settings",
            )
            self.process_complete_signal.emit(False)
            return

        self.log_message(
            logging.INFO,
            f"Searching GLL files in {gll_directory}",
        )

        # Convert to Path object for cross-platform compatibility
        gll_path = Path(gll_directory)
        if not gll_path.exists():
            self.log_message(
                logging.ERROR,
                f"Directory does not exist: {gll_directory}",
            )
            self.process_complete_signal.emit(False)
            return

        # Search for both .GLL and .gll files using pathlib
        gll_files = []
        for ext in [".GLL", ".gll"]:
            gll_paths = list(gll_path.rglob(f"*{ext}"))
            print(gll_paths)
            self.log_message(
                logging.INFO,
                f"Found {len(gll_paths)} GLL files with extension {ext}",
            )
            gll_files.extend(gll_paths)

        # Convert paths to strings using os.fspath() for cross-platform compatibility
        gll_files = [os.fspath(f) for f in gll_files]
        # Normalize paths to handle different path separators
        gll_files = [str(Path(f)) for f in gll_files]
        gll_files = list(set(gll_files))
        total_files = len(gll_files)

        if total_files == 0:
            self.log_message(
                logging.WARNING,
                "No GLL files found in the specified directory.",
            )
            self.process_complete_signal.emit(False)
            return

        self.log_message(
            logging.INFO,
            f"Found {total_files} GLL files.",
        )

        # Process each GLL file
        self.log_message(
            logging.INFO,
            f"Processing {total_files} GLL files, output will be saved to {self.settings.value('output_directory')}.",
        )
        missing_speaker_files = []
        for index, gll_file in enumerate(gll_files, 1):
            input_path = gll_file

            # Try to get speaker data from database
            speaker_data = self.speaker_db.get_speaker_data(input_path)

            if not speaker_data:
                # If no speaker data, request it
                missing_speaker_files.append(input_path)
                continue

            speaker_name = speaker_data["speaker_name"]
            if speaker_data.get("skip", False):
                self.log_message(
                    logging.INFO,
                    f"Skipping {speaker_name} ({input_path})",
                )
                continue

            # Extract speaker data
            try:
                output_dir = self.settings.value("output_directory")
                config_files = speaker_data.get("config_files", [])
                config_file = config_files[0] if config_files else None
                result = gll_extract_speaker(
                    output_dir, speaker_name, input_path, config_file
                )
                if result:
                    self.log_message(
                        logging.INFO,
                        f"Successfully processed {speaker_name} ({input_path})",
                    )
                else:
                    self.log_message(
                        logging.ERROR,
                        f"Failed to process {speaker_name} ({input_path})",
                    )
            except Exception as e:
                self.log_message(
                    logging.ERROR,
                    f"Error processing {speaker_name} ({input_path}): {str(e)}",
                )

            # Update progress
            progress = int((index / total_files) * 100)
            self.progress_signal.emit(progress)

            if self.stop_process:
                break

        # If there are missing speaker files, emit signal
        if missing_speaker_files:
            self.speaker_data_required_signal.emit(missing_speaker_files)
            self.process_complete_signal.emit(False)
        else:
            self.process_complete_signal.emit(True)

    def stop_processing(self):
        self.stop_process = True
