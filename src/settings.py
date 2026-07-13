from functools import lru_cache
from typing import final

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    encryption_key: str

    app_base_url: str = 'http://localhost:8000'
    google_client_id: str = ''
    google_client_secret: str = ''

    gemini_api_key: str = ''
    gemini_model: str = 'gemini-2.5-flash'
    groq_api_key: str = ''
    groq_model: str = 'llama-3.3-70b-versatile'


@lru_cache()  # get it from memory
def get_settings() -> Settings:
    return Settings()
