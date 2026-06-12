from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import final


@final
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=('.prod.env', '.dev.env'),  # first search .dev.env, then .prod.env
        env_file_encoding='utf-8')

    debug: bool = True
    redis_url: str = 'redis://localhost:6379/0'
    bot_token: str = '1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    base_webhook_url: str | None = None
    webhook_path: str | None = None
    telegram_my_token: str | None = None

    database_url: str = 'postgresql+asyncpg://user:password@localhost:5432/garazh'


@lru_cache()  # get it from memory
def get_settings() -> Settings:
    return Settings()
