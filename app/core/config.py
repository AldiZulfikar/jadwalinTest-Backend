from typing import Literal, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "JadwalinTest"
    APP_SLOGAN: str = "Jadwal Terkendali, Aplikasi Siap Berlari!"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000

    # CORS Configuration
    CORS_ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        description="Comma-separated list of allowed CORS origins"
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/booking_db",
        description="SQLAlchemy database connection string"
    )

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="supersecret_jwt_key_change_in_production_ptrsv_2026",
        description="Secret key used for signing JWT tokens"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="Algorithm used for signing JWT tokens"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60,
        description="Expiration time for access tokens in minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Expiration time for refresh tokens in days"
    )

    # Email Service
    EMAIL_ENABLED: bool = Field(
        default=True,
        description="Master toggle for email notifications"
    )
    EMAIL_PROVIDER: Literal["smtp", "graph"] = Field(
        default="smtp",
        description="Active email provider: 'smtp' or 'graph'"
    )

    # SMTP Credentials
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "no-reply@example.com"
    SMTP_USE_TLS: bool = True

    # Microsoft Graph Credentials (Placeholder)
    GRAPH_TENANT_ID: str = ""
    GRAPH_CLIENT_ID: str = ""
    GRAPH_CLIENT_SECRET: str = ""

    # Notification Target
    QA_NOTIFICATION_EMAIL: str = "qa-team@example.com"
    QA_EMAIL: str = "qa-team@example.com"

    @property
    def get_cors_origins(self) -> List[str]:
        if not self.CORS_ALLOWED_ORIGINS:
            return ["http://localhost:3000"]
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()
