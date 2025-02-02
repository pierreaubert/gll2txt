
from app_misc import (
    create_default_settings,
    validate_settings,
    get_windows_documents_path,
)


def test_create_default_settings():
    """Test creating default settings"""
    settings = create_default_settings()
    assert settings is not None
    assert settings.value("gll_files_directory") is not None


def test_validate_settings_empty():
    """Test validating empty settings"""
    settings = create_default_settings()
    settings.clear()

    result, errors = validate_settings(settings)
    assert not result
    assert len(errors) > 0
    assert any("not set" in error for error in errors)


def test_validate_settings_invalid_directory():
    """Test validating settings with invalid directory"""
    settings = create_default_settings()
    settings.setValue("gll_files_directory", "/invalid/path")

    result, errors = validate_settings(settings)
    assert not result
    assert len(errors) > 0
    assert any("Invalid GLL files directory" in error for error in errors)


def test_validate_settings_valid(temp_dir):
    """Test validating valid settings"""
    settings = create_default_settings()
    settings.setValue("gll_files_directory", str(temp_dir))
    settings.setValue("ease_binary_path", str(temp_dir))
    settings.setValue("output_directory", str(temp_dir))

    result, errors = validate_settings(settings)
    assert result
    assert len(errors) == 0


def test_get_windows_documents_path():
    """Test getting Windows Documents path"""
    path = get_windows_documents_path()
    assert path is not None
    assert isinstance(path, str)
