from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://gec:gec_secret@localhost:5432/gec_db"
    SECRET_KEY: str = "changeme_in_production_use_openssl_rand"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    UPLOADS_DIR: str = "uploads"


settings = Settings()
