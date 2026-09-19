from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Library Management API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    api_prefix: str = "/api"

    database_url: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    max_active_borrowings: int = 3
    borrow_duration_days: int = 14

    login_rate_limit_per_minute: int = 10
    register_rate_limit_per_minute: int = 20

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL must be set. Copy .env.example to .env and fill it in."
            )
        if len(self.jwt_secret_key) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters. "
                "Generate one with: openssl rand -hex 32"
            )
        return self


settings = Settings()