import os

from database import SpeakerDatabase


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

    assert data is not None
    assert data["speaker_name"] == test_name
    assert data["config_files"] == test_configs

    # Update
    new_name = "Updated Speaker"
    new_configs = ["new_config.txt"]
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
    test_configs = ["config1.txt"]

    # Create a speaker
    db.save_speaker_data(test_file, test_name, test_configs)

    # Initially skip should be False
    data = db.get_speaker_data(test_file)
    assert not data["skip"]

    # Set skip to True
    db.skip_speaker(test_file, True)
    data = db.get_speaker_data(test_file)
    assert data["skip"]

    # Set skip back to False
    db.skip_speaker(test_file, False)
    data = db.get_speaker_data(test_file)
    assert not data["skip"]


def test_list_all_speakers(db):
    """Test listing all speakers"""
    # Add multiple speakers
    speakers = [
        ("test1.gll", "Speaker 1", ["config1.txt"]),
        ("test2.gll", "Speaker 2", ["config2.txt"]),
        ("test3.gll", "Speaker 3", ["config3.txt"]),
    ]

    for config_file, name, configs in speakers:
        db.save_speaker_data(config_file, name, configs)

    # List all speakers
    all_speakers = db.list_all_speakers()

    # Verify all speakers are returned
    assert len(all_speakers) == len(speakers)
    for config_file, name, configs in speakers:
        speaker_data = db.get_speaker_data(config_file)
        assert speaker_data is not None
        assert speaker_data["speaker_name"] == name
        assert speaker_data["config_files"] == configs


def test_default_database_path():
    """Test that the default database path is in Documents"""
    db_path = os.path.join(os.path.expanduser("~"), "Documents", "GLL2TXT_Speakers.db")
    db = SpeakerDatabase(db_path)
    assert os.path.exists(db_path)
    db.remove_database()
