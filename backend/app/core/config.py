from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RevSplit - Programmatic Cashback & Affiliate Arbitrage Engine"
    ENV: str = "production"
    DEBUG: bool = False
    PORT: int = 8000

    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SECRET_KEY: Optional[str] = None
    SUPABASE_JWKS_URL: str = ""

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgrespassword"
    POSTGRES_DB: str = "revsplit_db"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    CLICK_TOKEN_TTL_SECONDS: int = 86400

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CLICK_TOPIC: str = "click.events"
    KAFKA_POSTBACK_TOPIC: str = "postback.confirmed"

    DEFAULT_USER_CASHBACK_PERCENT: float = 70.0
    DEFAULT_PLATFORM_REVENUE_PERCENT: float = 30.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
