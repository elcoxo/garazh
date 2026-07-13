import json
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.redis import redis_client
from models.app_settings import AppSettings
from models.enums import AIProvider

_CACHE_KEY = 'app_settings:ai'
_CACHE_TTL = 300


@dataclass(frozen=True, slots=True)
class AISettings:
    main: AIProvider
    enabled: bool


async def get_ai_settings(session: AsyncSession) -> AISettings:
    cached = await _read_cache()
    if cached is not None:
        return cached

    settings = await _read_db(session)
    await _write_cache(settings)
    return settings


async def invalidate_ai_settings() -> None:
    await redis_client.delete(_CACHE_KEY)


async def _read_cache() -> AISettings | None:
    raw = await redis_client.get(_CACHE_KEY)
    if raw is None:
        return None
    data = json.loads(raw)
    return AISettings(main=AIProvider(data['main']), enabled=data['enabled'])


async def _write_cache(settings: AISettings) -> None:
    payload = json.dumps({'main': settings.main.value, 'enabled': settings.enabled})
    await redis_client.setex(_CACHE_KEY, _CACHE_TTL, payload)


async def _read_db(session: AsyncSession) -> AISettings:
    result = await session.execute(select(AppSettings).limit(1))
    row = result.scalar_one()
    return AISettings(main=row.ai_priority, enabled=row.ai_enabled)
