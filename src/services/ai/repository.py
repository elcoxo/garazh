from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.redis import redis_client
from db.session import AsyncSessionFactory
from models.ai_model import AIModel
from models.app_settings import AppSettings
from models.enums import AIProvider

_CACHE_KEY = 'app_settings:ai'
_CACHE_TTL = 300


class ModelRef(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: int
    provider: AIProvider
    name: str


class AISettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    models: tuple[ModelRef, ...]
    enabled: bool


async def get_ai_settings(session: AsyncSession) -> AISettings:
    if (cached := await _read_cache()) is not None:
        return cached

    settings = await _read_db(session)
    await _write_cache(settings)
    return settings


async def invalidate_ai_settings() -> None:
    await redis_client.delete(_CACHE_KEY)


async def save_last_used_model(ai_model_id: int, model_name: str | None) -> None:
    async with AsyncSessionFactory() as session:
        await session.execute(update(AIModel).where(AIModel.id == ai_model_id).values(last_used_model=model_name))
        await session.commit()


async def replace_last_used_model(ai_model_id: int, new_name: str | None) -> None:
    await save_last_used_model(ai_model_id, new_name)
    await invalidate_ai_settings()


async def _read_cache() -> AISettings | None:
    raw = await redis_client.get(_CACHE_KEY)
    return AISettings.model_validate_json(raw) if raw else None


async def _write_cache(settings: AISettings) -> None:
    await redis_client.setex(_CACHE_KEY, _CACHE_TTL, settings.model_dump_json())


async def _read_db(session: AsyncSession) -> AISettings:
    result = await session.execute(select(AppSettings).limit(1))
    row = result.scalar_one()
    result = await session.execute(
        select(AIModel).where(AIModel.is_active).order_by(AIModel.order, AIModel.id)
    )
    models = []
    for ai_model in result.scalars():
        models.append(ModelRef(
            id=ai_model.id, provider=ai_model.provider, name=ai_model.last_used_model or ai_model.name,
        ))
    return AISettings(models=tuple(models), enabled=row.ai_enabled)
