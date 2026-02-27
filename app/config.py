"""Application settings loaded from environment (and optional .env file)."""

from dotenv import load_dotenv
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file into environment if present (no-op if not found)
load_dotenv()


class Settings(BaseSettings):
    """Validated config from env. Use get_settings() to access."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Shared secret used by callers as a Bearer token. Required.
    geology_engine_api_key: SecretStr = Field(
        ...,
        min_length=1,
        description="Shared API key sent by callers as a Bearer token",
    )

    def get_api_key_str(self) -> str:
        """Return the raw key value. Never log this."""
        return self.geology_engine_api_key.get_secret_value()


_settings: Settings | None = None


def get_settings() -> Settings:
    """Cached settings instance. Fails at first use if env is invalid."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
