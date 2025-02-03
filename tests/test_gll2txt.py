import sys
import pytest
from gll2txt import extract_speaker

windows_only = pytest.mark.skipif(
    sys.platform != "win32", reason="GLL extraction only works on Windows"
)


@windows_only
def test_extract_speaker_invalid_file(caplog, temp_dir):
    """Test extracting speaker from invalid file"""
    result = extract_speaker(
        gll_file="/invalid/path/test.GLL",
        speaker_name="Test Speaker",
        config_file="config.txt",
        output_dir=str(temp_dir),
    )
    assert result is None
    assert "Error opening GLL file" in caplog.text


@windows_only
def test_extract_speaker_no_speaker(temp_dir, caplog):
    """Test extracting speaker from file with no speaker info"""
    test_file = temp_dir / "test.GLL"
    test_file.touch()

    result = extract_speaker(
        gll_file=str(test_file),
        speaker_name="Test Speaker",
        config_file="config.txt",
        output_dir=str(temp_dir),
    )
    assert result is None
    assert "No speaker information found" in caplog.text
