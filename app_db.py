import os
import sqlite3
import logging
import threading
from PySide6.QtCore import QObject, Signal

from app_misc import get_windows_documents_path


class SpeakerDatabase(QObject):
    """Database for storing speaker information"""

    CURRENT_SCHEMA_VERSION = "0.2"
    log_signal = Signal(int, str)  # level and message

    def __init__(self, db_path=None):
        """
        Initialize the database connection.

        Args:
            db_path (str, optional): Path to the database file.
            If None, uses default path in Documents.
        """
        super().__init__()
        if db_path is None:
            db_path = os.path.join(get_windows_documents_path(), "GLL2TXT_Speakers.db")

        self.db_path = db_path
        self.log_message(logging.INFO, f"Opening database at {self.db_path}")

        # Thread-local storage for connections
        self._local = threading.local()

        # Initialize schema in main thread
        self._get_connection()
        self._initialize_schema()

    def _get_connection(self):
        """Get thread-local connection"""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            self._local.connection = sqlite3.connect(self.db_path, isolation_level=None)
            self._local.cursor = self._local.connection.cursor()
            self.log_message(
                logging.DEBUG,
                f"Created new database connection for thread {threading.current_thread().name}",
            )
        return self._local.connection, self._local.cursor

    def _initialize_schema(self):
        """Initialize database schema"""
        connection, cursor = self._get_connection()

        # Create schema version table if it doesn't exist
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Get current schema version
        cursor.execute(
            "SELECT version FROM schema_version ORDER BY updated_at DESC LIMIT 1"
        )
        result = cursor.fetchone()
        current_version = result[0] if result else "0.1"

        # Perform migrations if needed
        if current_version != self.CURRENT_SCHEMA_VERSION:
            self.log_message(
                logging.INFO,
                f"Database needs migration from {current_version} to {self.CURRENT_SCHEMA_VERSION}",
            )
            self._migrate_database(current_version)

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

    def _migrate_database(self, current_version):
        """
        Migrate database from current version to latest version.

        Args:
            current_version (str): Current schema version
        """
        connection, cursor = self._get_connection()
        try:
            # Start transaction
            cursor.execute("BEGIN TRANSACTION")

            if current_version == "0.1":
                self.log_message(logging.INFO, "Migrating database from 0.1 to 0.2...")
                # Add skip column to speakers table
                cursor.execute(
                    """
                    ALTER TABLE speakers 
                    ADD COLUMN skip BOOLEAN DEFAULT 0
                    """
                )
                current_version = "0.2"

            # Update schema version
            cursor.execute(
                """
                INSERT INTO schema_version (version) 
                VALUES (?)
                """,
                (self.CURRENT_SCHEMA_VERSION,),
            )

            # Commit transaction
            cursor.execute("COMMIT")
            self.log_message(
                logging.INFO,
                f"Database successfully migrated to version {self.CURRENT_SCHEMA_VERSION}",
            )

        except Exception as e:
            self.log_message(logging.ERROR, f"Error during database migration: {e}")
            # Rollback on error
            cursor.execute("ROLLBACK")
            raise

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
        if hasattr(self, "_local"):
            if hasattr(self._local, "connection") and self._local.connection:
                self.log_message(
                    logging.DEBUG,
                    f"Closing database connection for thread {threading.current_thread().name}",
                )
                self._local.connection.close()
