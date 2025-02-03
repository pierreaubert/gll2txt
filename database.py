"""Database module for storing speaker information"""

import os
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import sessionmaker
from PySide6.QtCore import QObject, Signal

from models.speaker import Base, Speaker
from models.config_file import ConfigFile


class SpeakerDatabase(QObject):
    """Database for storing speaker information"""

    log_signal = Signal(int, str)  # level and message

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database connection and schema

        Args:
            db_path (str, optional): Path to SQLite database file.
                                   If None, use default path in user's home directory.
        """
        super().__init__()
        try:
            # Set database path
            if db_path is None:
                db_path = str(Path.home() / "Documents" / "GLL2TXT_Speakers.db")
            self.log_message(logging.DEBUG, f"Using database path: {db_path}")

            self.db_path = db_path

            # Ensure directory exists
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                self.log_message(
                    logging.DEBUG, f"Creating database directory: {db_dir}"
                )
                try:
                    os.makedirs(db_dir)
                except Exception as e:
                    self.log_message(
                        logging.ERROR, f"Failed to create database directory: {db_dir}"
                    )
                    raise RuntimeError(
                        f"Could not create database directory: {db_dir}"
                    ) from e

            # Create engine and session factory
            self.log_message(logging.DEBUG, "Creating database engine")
            try:
                self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
                self.Session = sessionmaker(bind=self.engine)

                # Create tables
                self.log_message(logging.DEBUG, "Creating database tables")
                Base.metadata.create_all(self.engine)

                # Verify tables exist
                with self.engine.connect() as conn:
                    # Get list of tables
                    tables = Base.metadata.tables.keys()
                    self.log_message(
                        logging.INFO, f"Created tables: {', '.join(tables)}"
                    )

                    # Verify each table exists
                    for table in tables:
                        result = conn.execute(
                            text(
                                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"
                            )
                        )
                        if not result.fetchone():
                            raise RuntimeError(f"Table {table} was not created")
                        self.log_message(
                            logging.DEBUG, f"Verified table exists: {table}"
                        )

            except Exception as e:
                self.log_message(logging.ERROR, "Failed to initialize database")
                raise RuntimeError("Could not initialize database") from e

        except Exception:
            self.log_message(logging.ERROR, "Database initialization failed")
            raise

    def log_message(self, level: int, message: str):
        """Helper method to emit log messages with level and also log to system logger"""
        # Emit signal for Qt UI
        self.log_signal.emit(level, message)
        # Also log to system logger
        logging.log(level, message)

    def save_speaker_data(
        self,
        gll_file,
        speaker_name,
        config_files=None,
        skip=False,
        sensitivity=None,
        impedance=None,
        weight=None,
        height=None,
        width=None,
        depth=None,
    ):
        """Save speaker data to database"""
        try:
            session = self.Session()
            speaker = session.query(Speaker).filter_by(gll_file=gll_file).first()
            if not speaker:
                speaker = Speaker(gll_file=gll_file)

            speaker.speaker_name = speaker_name
            speaker.skip = skip
            speaker.sensitivity = sensitivity
            speaker.impedance = impedance
            speaker.weight = weight
            speaker.height = height
            speaker.width = width
            speaker.depth = depth

            # Handle config files
            if config_files is not None:
                # Clear existing config files
                speaker.config_files = []
                # Add new config files
                for file_path in config_files:
                    config_file = ConfigFile(file_path=file_path, speaker=speaker)
                    speaker.config_files.append(config_file)

            if speaker not in session:
                session.add(speaker)
            session.commit()

            self.log_message(logging.INFO, f"Saved speaker data for {gll_file}")
            return True

        except Exception as e:
            self.log_message(logging.ERROR, f"Error saving speaker data: {str(e)}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_speaker_data(self, gll_file):
        """Get speaker data from database"""
        try:
            session = self.Session()
            speaker = session.query(Speaker).filter_by(gll_file=gll_file).first()
            if speaker:
                return {
                    "speaker_name": speaker.speaker_name,
                    "config_files": [cf.file_path for cf in speaker.config_files],
                    "skip": speaker.skip,
                    "sensitivity": speaker.sensitivity,
                    "impedance": speaker.impedance,
                    "weight": speaker.weight,
                    "height": speaker.height,
                    "width": speaker.width,
                    "depth": speaker.depth,
                }
            return None
        except Exception as e:
            self.log_message(logging.ERROR, f"Error getting speaker data: {str(e)}")
            return None
        finally:
            session.close()

    def list_all_speakers(self) -> List[Dict[str, Any]]:
        """
        Get a list of all speakers in the database.

        Returns:
            list: List of dictionaries containing speaker data
        """
        with self.Session() as session:
            speakers = session.execute(select(Speaker)).scalars().all()
            return [
                {
                    "gll_file": speaker.gll_file,
                    "speaker_name": speaker.speaker_name,
                    "config_files": [cf.file_path for cf in speaker.config_files],
                    "skip": speaker.skip,
                    "sensitivity": speaker.sensitivity,
                    "impedance": speaker.impedance,
                    "weight": speaker.weight,
                    "height": speaker.height,
                    "width": speaker.width,
                    "depth": speaker.depth,
                }
                for speaker in speakers
            ]

    def delete_speaker(self, gll_file: str):
        """
        Delete a speaker from the database.

        Args:
            gll_file (str): Path to the GLL file
        """
        with self.Session() as session:
            speaker = session.get(Speaker, gll_file)
            if speaker:
                session.delete(speaker)
                session.commit()

    def cleanup(self):
        """Clean up database resources"""
        try:
            if hasattr(self, "Session"):
                # Close all connections
                self.Session.close_all()
                if hasattr(self, "engine"):
                    self.engine.dispose()
                delattr(self, "Session")
                delattr(self, "engine")
        except Exception as e:
            self.log_message(logging.ERROR, f"Error during database cleanup: {str(e)}")

    def remove_database(self):
        """Remove the database file"""
        try:
            self.cleanup()
            if hasattr(self, "db_path") and os.path.exists(self.db_path):
                os.remove(self.db_path)
        except Exception as e:
            self.log_message(logging.ERROR, f"Error removing database file: {str(e)}")

    def __del__(self):
        """Cleanup engine on object destruction"""
        try:
            self.cleanup()
        except:
            # Suppress errors during deletion
            pass
