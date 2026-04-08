from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    # App
    app_env: str = "development"
    secret_key: str
    allowed_origins: str = "http://localhost:3000"

    # Database — individual parts (used locally with Docker)
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""

    # Full connection URL — set DATABASE_URL on Render/cloud platforms
    # This takes priority over individual DB_* variables
    db_url_env: str = Field(default="", validation_alias="DATABASE_URL")

    # MSG91 (SMS)
    msg91_authkey: str = ""
    msg91_otp_template_id: str = ""
    msg91_sender_id: str = "NIRVIZ"

    # Gmail OTP
    gmail_sender: str = ""
    gmail_app_password: str = ""

    # Shopkeeper
    shopkeeper_phone: str = ""
    shopkeeper_email: str = ""

    # Admin dashboard
    admin_password: str = "admin123"

    # OTP
    otp_expiry_minutes: int = 5
    otp_max_attempts: int = 3
    otp_cooldown_minutes: int = 10

    # Frontend
    next_public_api_url: str = "http://localhost:8000"
    next_public_google_review_url: str = ""

    def _build_url(self, raw: str, driver: str) -> str:
        """Convert a plain postgres:// URL to the correct driver URL with SSL."""
        url = raw.replace("postgres://", "postgresql://", 1)
        if driver == "asyncpg":
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)
            if "ssl=" not in url and "sslmode=" not in url:
                sep = "&" if "?" in url else "?"
                url += f"{sep}ssl=require"
        else:
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
            if "postgresql+psycopg2://" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            if "sslmode=" not in url:
                sep = "&" if "?" in url else "?"
                url += f"{sep}sslmode=require"
        return url

    @property
    def database_url(self) -> str:
        """Async URL for SQLAlchemy (asyncpg driver)."""
        if self.db_url_env:
            return self._build_url(self.db_url_env, "asyncpg")
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL for Alembic migrations (psycopg2 driver)."""
        if self.db_url_env:
            return self._build_url(self.db_url_env, "psycopg2")
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?sslmode=require"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
