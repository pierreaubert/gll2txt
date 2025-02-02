import os
import sqlite3
import logging

from PySide6.QtCore import QObject, Signal



class SpeakerDatabase(QObject):
    """Database for storing speaker information"""

    log_signal = Signal(int, str)  # level and message

    def __init__(self, db_path=None):
        """
        Initialize database connection and schema

        Args:
            db_path (str, optional): Path to the database file.
            If None, uses default path in Documents.
        """
        super().__init__()

        # Set database path
        if db_path is None:
            home = os.path.expanduser("~")
            db_path = os.path.join(home, ".gll2txt.db")

        self.db_path = db_path
        self.log_message(logging.INFO, f"Opening database at {self.db_path}")

        # Create database directory if needed
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        # Initialize schema
        self._initialize_schema()

    def _get_connection(self):
        """Get a new database connection"""
        connection = sqlite3.connect(self.db_path)
        cursor = connection.cursor()
        return connection, cursor

    def _initialize_schema(self):
        """Initialize database schema"""
        self._create_tables()

    def log_message(self, level, message):
        """Helper method to emit log messages with level"""
        self.log_signal.emit(level, message)

    def _create_tables(self):
        """Create the necessary tables if they don't exist"""
        self.log_message(logging.INFO, "Creating/verifying database tables")
        connection, cursor = self._get_connection()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS speakers (
                gll_file TEXT PRIMARY KEY,
                speaker_name TEXT NOT NULL,
                skip BOOLEAN DEFAULT 0,
                UNIQUE(gll_file)
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config_files (
                gll_file TEXT,
                config_file TEXT,
                FOREIGN KEY(gll_file) REFERENCES speakers(gll_file),
                UNIQUE(gll_file, config_file)
            )
            """
        )
        connection.commit()

    def save_speaker_data(self, gll_file, speaker_name, config_files, skip=False):
        """
        Save or update speaker data for a specific GLL file

        Args:
            gll_file (str): Path to the GLL file
            speaker_name (str): Name of the speaker
            config_files (list): List of config file paths
            skip (bool, optional): Whether to skip this GLL file. Defaults to False.
        """
        connection, cursor = self._get_connection()
        try:
            self.log_message(logging.INFO, f"Saving speaker data for {gll_file}")
            cursor.execute("BEGIN TRANSACTION")

            cursor.execute(
                """
                INSERT OR REPLACE INTO speakers 
                (gll_file, speaker_name, skip) 
                VALUES (?, ?, ?)
                """,
                (gll_file, speaker_name, skip),
            )

            # Handle config files
            cursor.execute("DELETE FROM config_files WHERE gll_file = ?", (gll_file,))
            for config_file in config_files:
                cursor.execute(
                    """
                    INSERT INTO config_files (gll_file, config_file)
                    VALUES (?, ?)
                    """,
                    (gll_file, config_file),
                )

            cursor.execute("COMMIT")
            self.log_message(
                logging.INFO, f"Successfully saved speaker data for {gll_file}"
            )
        except Exception as e:
            self.log_message(logging.ERROR, f"Error saving speaker data: {e}")
            cursor.execute("ROLLBACK")
            raise

    def get_speaker_data(self, gll_file):
        """
        Get speaker data for a given GLL file.

        Args:
            gll_file (str): Path to the GLL file

        Returns:
            dict: Speaker data including name and config files, or None if not found
        """
        connection, cursor = self._get_connection()
        cursor.execute(
            "SELECT speaker_name, skip FROM speakers WHERE gll_file = ?",
            (gll_file,),
        )
        speaker_row = cursor.fetchone()

        if speaker_row:
            # Get config files
            cursor.execute(
                "SELECT config_file FROM config_files WHERE gll_file = ?",
                (gll_file,),
            )
            config_files = [row[0] for row in cursor.fetchall()]

            return {
                "speaker_name": speaker_row[0],
                "skip": bool(speaker_row[1]),
                "config_files": config_files,
            }

        return None

    def list_all_speakers(self):
        """
        Get a list of all speakers in the database.

        Returns:
            list: List of dictionaries containing speaker data
        """
        connection, cursor = self._get_connection()
        cursor.execute("SELECT gll_file, speaker_name, skip FROM speakers")
        results = cursor.fetchall()

        speakers = []
        for row in results:
            # Get config files for this speaker
            cursor.execute(
                "SELECT config_file FROM config_files WHERE gll_file = ?",
                (row[0],),
            )
            config_files = [r[0] for r in cursor.fetchall()]

            speakers.append(
                {
                    "gll_file": row[0],
                    "speaker_name": row[1],
                    "skip": bool(row[2]),
                    "config_files": config_files,
                }
            )

        return speakers

    def delete_speaker(self, gll_file):
        """
        Delete a speaker from the database.

        Args:
            gll_file (str): Path to the GLL file
        """
        connection, cursor = self._get_connection()
        self.log_message(
            logging.INFO, f"Attempting to delete speaker data for {gll_file}"
        )
        try:
            cursor.execute("BEGIN TRANSACTION")
            cursor.execute("DELETE FROM config_files WHERE gll_file = ?", (gll_file,))
            cursor.execute("DELETE FROM speakers WHERE gll_file = ?", (gll_file,))
            cursor.execute("COMMIT")
        except Exception as e:
            cursor.execute("ROLLBACK")
            self.log_message(logging.ERROR, f"Error deleting speaker: {e}")
            raise

    def __del__(self):
        """Cleanup connections on object destruction"""
        pass
