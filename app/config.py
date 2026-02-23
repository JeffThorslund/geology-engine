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

    # Supabase JWT secret (HS256) used to verify access tokens. Required for auth.
    supabase_jwt_secret: SecretStr = Field(
        ...,
        min_length=1,
        description="Supabase project JWT secret (Settings > API > JWT Secret)",
    )

    def get_supabase_jwt_secret_str(self) -> str:
        """Use in code that needs the raw secret (e.g. jwt.decode). Never log this."""
        return self.supabase_jwt_secret.get_secret_value()


_settings: Settings | None = None


def get_settings() -> Settings:
    """Cached settings instance. Fails at first use if env is invalid."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
