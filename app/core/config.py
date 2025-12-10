from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30  # 30 minutes
    refresh_token_expire_days: int = 14  # 14 days
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
