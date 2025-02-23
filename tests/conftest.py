import tempfile
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from database import SpeakerDatabase


@pytest.fixture(scope="session")
def qapp():
    """Create a Qt Application for tests"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def temp_db_path(temp_dir):
    """Create a temporary database path"""
    return temp_dir / "test.db"


@pytest.fixture
def db(temp_db_path):
    """Create a temporary test database instance"""
    db = SpeakerDatabase(str(temp_db_path))
    yield db
    db.remove_database()


@pytest.fixture
def gll_files(temp_dir):
    """Create temporary GLL files for testing"""
    files = []
    for i in range(3):
        file_path = temp_dir / f"test{i}.GLL"
        file_path.touch()
        files.append(str(file_path))
    return files
