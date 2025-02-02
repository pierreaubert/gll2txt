import os
import pytest
from pathlib import Path
from database import SpeakerDatabase


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path"""
    return tmp_path / "test.db"


@pytest.fixture
def db(temp_db_path):
    """Create a test database instance"""
    return SpeakerDatabase(str(temp_db_path))


def test_new_database_creation(temp_db_path):
    """Test that a new database is created with the correct schema"""
    # Database shouldn't exist yet
    assert not os.path.exists(temp_db_path)

    # Creating database instance should create the file
    db = SpeakerDatabase(str(temp_db_path))
    assert os.path.exists(temp_db_path)

    # Verify tables exist by adding and querying data
    test_file = "test.gll"
    test_name = "Test Speaker"
    test_configs = ["config1.txt", "config2.txt"]

    db.save_speaker_data(test_file, test_name, test_configs)
    data = db.get_speaker_data(test_file)

    assert data is not None
    assert data["speaker_name"] == test_name
    assert data["config_files"] == test_configs

    # Clean up
    db.remove_database()


def test_speaker_crud_operations(db):
    """Test Create, Read, Update, Delete operations for speakers"""
    # Create
    test_file = "test.gll"
    test_name = "Test Speaker"
    test_configs = ["config1.txt"]

    db.save_speaker_data(test_file, test_name, test_configs)
    data = db.get_speaker_data(test_file)

    assert data["speaker_name"] == test_name
    assert data["config_files"] == test_configs

    # Update
    new_name = "Updated Speaker"
    new_configs = ["config2.txt", "config3.txt"]
    db.save_speaker_data(test_file, new_name, new_configs)
    data = db.get_speaker_data(test_file)

    assert data["speaker_name"] == new_name
    assert data["config_files"] == new_configs

    # Delete
    db.delete_speaker(test_file)
    assert db.get_speaker_data(test_file) is None


def test_skip_flag(db):
    """Test the skip flag functionality"""
    test_file = "test.gll"
    test_name = "Test Speaker"
    test_configs = ["config.txt"]

    # Create with skip=True
    db.save_speaker_data(test_file, test_name, test_configs, skip=True)
    data = db.get_speaker_data(test_file)
    assert data["skip"]

    # Update skip to False
    db.skip_speaker(test_file, False)
    data = db.get_speaker_data(test_file)
    assert not data["skip"]


def test_list_all_speakers(db):
    """Test listing all speakers"""
    # Add multiple speakers
    speakers = [
        ("speaker1.gll", "Speaker 1", ["config1.txt"]),
        ("speaker2.gll", "Speaker 2", ["config2.txt", "config3.txt"]),
        ("speaker3.gll", "Speaker 3", []),
    ]

    for gll_file, name, configs in speakers:
        db.save_speaker_data(gll_file, name, configs)

    # List all speakers
    all_speakers = db.list_all_speakers()
    assert len(all_speakers) == len(speakers)

    for speaker in all_speakers:
        assert speaker["gll_file"] in [s[0] for s in speakers]
        assert speaker["speaker_name"] in [s[1] for s in speakers]


def test_default_database_path():
    """Test that the default database path is in Documents"""
    db = SpeakerDatabase()
    assert "Documents" in db.db_path
    assert "GLL2TXT_Speakers.db" in db.db_path
    db.remove_database()
