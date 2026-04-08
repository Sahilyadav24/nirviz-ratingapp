from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_file_override=False,  # env vars always take priority over .env file
    )

    # App
    app_env: str = "development"
    secret_key: str
    allowed_origins: str = "http://localhost:3000"

    # Database
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str

    # MSG91 (SMS — OTP + notifications)
    # Optional in development — mock mode is used when these are not set
    msg91_authkey: str = ""
    msg91_otp_template_id: str = ""
    msg91_sender_id: str = "NIRVIZ"

    # Gmail OTP Service (Testing)
    gmail_sender: str = ""
    gmail_app_password: str = ""

    # Shopkeeper
    shopkeeper_phone: str
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

    @property
    def database_url(self) -> str:
        """Async URL for SQLAlchemy (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync URL for Alembic migrations."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
