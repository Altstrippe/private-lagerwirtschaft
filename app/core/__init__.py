from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="local", alias="APP_ENV")
    app_title: str = Field(default="Private Lagerwirtschaft", alias="APP_TITLE")
    database_url: str = Field(alias="DATABASE_URL")

    app_username: str = Field(alias="APP_USERNAME")
    app_password: str = Field(alias="APP_PASSWORD")
    app_secret_key: str = Field(alias="APP_SECRET_KEY")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()