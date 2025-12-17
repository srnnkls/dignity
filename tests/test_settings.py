"""Tests for settings module."""

from __future__ import annotations

from pathlib import Path

import pytest


def test_settings_default_specs_dir() -> None:
    """Settings should have specs_dir default to Path('specs')."""
    from dignity.settings import Settings

    settings = Settings()
    assert settings.specs_dir == Path("specs")


def test_settings_active_dir_property() -> None:
    """Settings.active_dir should return specs_dir / 'active'."""
    from dignity.settings import Settings

    settings = Settings()
    assert settings.active_dir == settings.specs_dir / "active"


def test_settings_archive_dir_property() -> None:
    """Settings.archive_dir should return specs_dir / 'archive'."""
    from dignity.settings import Settings

    settings = Settings()
    assert settings.archive_dir == settings.specs_dir / "archive"


def test_settings_from_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load specs_dir from DIGNITY_SPECS_DIR env var."""
    from dignity.settings import Settings

    monkeypatch.setenv("DIGNITY_SPECS_DIR", "/custom/specs/path")
    settings = Settings()
    assert settings.specs_dir == Path("/custom/specs/path")


def test_settings_from_toml_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings should load specs_dir from dignity.toml file."""
    from dignity.settings import Settings

    toml_content = 'specs_dir = "custom_specs"\n'
    toml_file = tmp_path / "dignity.toml"
    toml_file.write_text(toml_content)

    monkeypatch.chdir(tmp_path)
    settings = Settings()
    assert settings.specs_dir == Path("custom_specs")


def test_get_settings_returns_settings_instance() -> None:
    """get_settings should return a Settings instance."""
    from dignity.settings import Settings, get_settings

    result = get_settings()
    assert isinstance(result, Settings)
