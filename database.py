"""Database module for storing speaker information"""

import logging
import os
from typing import Any, Dict, List

from PySide6.QtCore import QObject, Signal
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from models.config_file import ConfigFile
from models.speaker import Base, Speaker


class SpeakerDatabase(QObject):
    """Database for storing speaker information"""

    log_signal = Signal(int, str)  # level and message

    def __init__(self, db_path: str):
        """
        Initialize the database connection and schema

        Args:
            db_path (str, optional): Path to SQLite database file.
                                   If None, use default path in user's home directory.
        """
        super().__init__()
        try:
            # Set database path
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

            # Create database engine
            self.engine = create_engine(f"sqlite:///{db_path}")

            # Run migrations
            from alembic import command
            from alembic.config import Config

            alembic_cfg = Config("alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
            command.upgrade(alembic_cfg, "head")

            # Create session maker
            self.Session = sessionmaker(bind=self.engine)

            # Create tables if they don't exist
            Base.metadata.create_all(self.engine)

            # Test database connection
            with self.Session() as session:
                session.execute(text("SELECT 1"))

        except Exception as e:
            self.log_message(logging.ERROR, f"Failed to initialize database: {str(e)}")
            raise RuntimeError("Could not initialize database") from e

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
        session = self.Session()
        try:
            speaker = session.query(Speaker).filter_by(gll_file=gll_file).first()
            if not speaker:
                speaker = Speaker(gll_file=gll_file)
                session.add(speaker)

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
                for config_file in config_files:
                    config_file = ConfigFile(config_file=config_file)
                    speaker.config_files.append(config_file)
                    session.add(config_file)

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
                    "config_files": [cf.config_file for cf in speaker.config_files],
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
                    "config_files": [cf.config_file for cf in speaker.config_files],
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

    def get_all_gll_files(self) -> List[str]:
        """
        Get a list of all GLL files in the database.

        Returns:
            list: List of GLL file paths
        """
        with self.Session() as session:
            speakers = session.execute(select(Speaker.gll_file)).scalars().all()
            return list(speakers)

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

    def skip_speaker(self, gll_file: str, skip: bool) -> bool:
        """
        Update the skip flag for a speaker.

        Args:
            gll_file (str): Path to the GLL file
            skip (bool): New skip flag value

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            session = self.Session()
            speaker = session.query(Speaker).filter_by(gll_file=gll_file).first()
            if not speaker:
                self.log_message(logging.ERROR, f"Speaker not found: {gll_file}")
                return False

            speaker.skip = skip
            session.commit()

            self.log_message(
                logging.INFO, f"Updated skip flag for {gll_file} to {skip}"
            )
            return True

        except Exception as e:
            self.log_message(logging.ERROR, f"Error updating skip flag: {str(e)}")
            session.rollback()
            return False
        finally:
            session.close()

    def cleanup(self):
        """Clean up database resources"""
        try:
            # Close all sessions
            from sqlalchemy.orm import close_all_sessions

            close_all_sessions()

            # Dispose engine
            if hasattr(self, "engine"):
                self.engine.dispose()
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
        except Exception:
            # Suppress errors during deletion
            pass
