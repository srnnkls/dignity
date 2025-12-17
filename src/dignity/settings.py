"""Settings module using pydantic-settings with TOML support."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict, TomlConfigSettingsSource


class Settings(BaseSettings):
    """Application settings with environment and TOML file support."""

    model_config = SettingsConfigDict(
        env_prefix="DIGNITY_",
        toml_file="dignity.toml",
    )

    specs_dir: Path = Field(default=Path("specs"))

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings,
        env_settings,
        dotenv_settings,
        file_secret_settings,
    ):
        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls),
        )

    @property
    def active_dir(self) -> Path:
        """Return the active specs directory."""
        return self.specs_dir / "active"

    @property
    def archive_dir(self) -> Path:
        """Return the archive specs directory."""
        return self.specs_dir / "archive"


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
