from pathlib import Path

from app_db import SpeakerDatabase


def test_speaker_database_init(temp_db_path):
    """Test SpeakerDatabase initialization"""
    db = SpeakerDatabase(str(temp_db_path))
    assert db.db_path == str(temp_db_path)
    assert Path(db.db_path).exists()
    db.remove_database()


def test_save_and_get_speaker_data(db):
    """Test saving and retrieving speaker data"""
    gll_file = "test.GLL"
    speaker_name = "Test Speaker"
    config_files = ["config1.txt", "config2.txt"]

    # Save data
    db.save_speaker_data(gll_file, speaker_name, config_files)

    # Retrieve data
    data = db.get_speaker_data(gll_file)
    assert data is not None
    assert data["speaker_name"] == speaker_name
    assert data["config_files"] == config_files
    assert not data["skip"]


def test_list_all_speakers(db):
    """Test listing all speakers"""
    speakers = [
        ("test1.GLL", "Speaker 1", ["config1.txt"]),
        ("test2.GLL", "Speaker 2", ["config2.txt"]),
    ]

    # Add speakers
    for gll_file, name, configs in speakers:
        db.save_speaker_data(gll_file, name, configs)

    # List speakers
    all_speakers = db.list_all_speakers()
    assert len(all_speakers) == len(speakers)
    for speaker in all_speakers:
        assert speaker["gll_file"] in [s[0] for s in speakers]
        assert speaker["speaker_name"] in [s[1] for s in speakers]


def test_delete_speaker(db):
    """Test deleting a speaker"""
    gll_file = "test.GLL"
    speaker_name = "Test Speaker"
    config_files = ["config.txt"]

    # Add and verify speaker exists
    db.save_speaker_data(gll_file, speaker_name, config_files)
    assert db.get_speaker_data(gll_file) is not None

    # Delete and verify speaker is gone
    db.delete_speaker(gll_file)
    assert db.get_speaker_data(gll_file) is None


def test_skip_speaker(db):
    """Test skip flag functionality"""
    gll_file = "test.GLL"
    speaker_name = "Test Speaker"
    config_files = ["config.txt"]

    # Add speaker with skip=True
    db.save_speaker_data(gll_file, speaker_name, config_files, skip=True)
    data = db.get_speaker_data(gll_file)
    assert data["skip"]

    # Update skip to False
    db.skip_speaker(gll_file, False)
    data = db.get_speaker_data(gll_file)
    assert not data["skip"]
