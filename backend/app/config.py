from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "RevSplit - Programmatic Cashback & Affiliate Arbitrage Engine"
    ENV: str = "production"
    DEBUG: bool = False
    PORT: int = 8000

    # Supabase Credentials
    SUPABASE_URL: str = "https://uzgazbnqlkkwqzqmnzts.supabase.co"
    SUPABASE_PUBLISHABLE_KEY: str = "sb_publishable_mF8aG-J2GnQtPHJTvWtMJA_XFte5xYK"
    SUPABASE_SECRET_KEY: Optional[str] = None
    SUPABASE_JWKS_URL: str = "https://uzgazbnqlkkwqzqmnzts.supabase.co/auth/v1/.well-known/jwks.json"

    # PostgreSQL Configuration
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "postgres"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    CLICK_TOKEN_TTL_SECONDS: int = 86400  # 24 hours TTL for click tracking sub_id

    # Kafka Configuration
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CLICK_TOPIC: str = "click.events"
    KAFKA_POSTBACK_TOPIC: str = "postback.confirmed"

    # Default Split Ratios
    DEFAULT_USER_CASHBACK_PERCENT: float = 70.0
    DEFAULT_PLATFORM_REVENUE_PERCENT: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
