from datetime import date
from functools import cache

from loguru import logger
from pydantic_ai import Agent
from pydantic_ai.exceptions import FallbackExceptionGroup, ModelAPIError, ModelHTTPError
from pydantic_ai.models.fallback import FallbackModel
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import AIProvider
from services.ai.catalog import build_model, find_available_model
from services.ai.exceptions import AIDisabledError, AIUnavailableError
from services.ai.repository import (
    ModelRef, get_ai_settings, replace_last_used_model, save_last_used_model,
)
from services.ai.schemas import EventDraft, EventExtractionResult

SYSTEM_PROMPT = (
    'Ты извлекаешь события из русскоязычных афиш и анонсов в Telegram. '
    'Заполняй поля строго по описанию каждого Field в схеме EventDraft. '
    'Если в посте несколько событий с разными датами — верни первое по времени. '
    'Если текст не про конкретное событие (новость, реклама, обсуждение, мем) — '
    'верни null вместо объекта.'
)


@cache
def _build_agent(refs: tuple[ModelRef, ...]) -> Agent[None, EventDraft | None]:
    models = []
    refs_by_name = {}
    for ref in refs:
        models.append(build_model(ref.provider, ref.name))
        refs_by_name[ref.name] = ref

    async def replace_gone_model(exc: Exception) -> bool:
        if isinstance(exc, ModelHTTPError) and (exc.status_code == 404 or 'decommissioned' in str(exc.body)):
            gone = refs_by_name[exc.model_name]
            new_name = await find_available_model(gone.provider, gone.name)
            await replace_last_used_model(gone.id, new_name)
            logger.warning(f'AI model {exc.model_name} is gone, replacement: {new_name}')
        return False

    model = FallbackModel(*models, fallback_on=[replace_gone_model, ModelAPIError])
    agent = Agent(model, output_type=EventDraft | None, system_prompt=SYSTEM_PROMPT)

    @agent.system_prompt
    def _today() -> str:
        return (
            f'Сегодня {date.today().isoformat()}. '
            f'Если в тексте только день и месяц без года — '
            f'выбери ближайшую дату в будущем относительно сегодня.'
        )

    return agent


async def extract_event(text: str, session: AsyncSession) -> EventExtractionResult:
    settings = await get_ai_settings(session)
    if not settings.enabled:
        raise AIDisabledError('AI is disabled in app_settings')
    if not settings.models:
        raise AIUnavailableError('No active models in ai_models')

    try:
        result = await _build_agent(settings.models).run(text)
    except (FallbackExceptionGroup, ModelAPIError) as e:
        raise AIUnavailableError('AI providers failed to extract the event') from e
    provider = AIProvider.GEMINI if result.response.provider_name == 'google' else AIProvider.GROQ
    if model_name := result.response.model_name:
        for ref in settings.models:
            if ref.provider == provider and model_name.startswith(ref.name):
                await save_last_used_model(ref.id, model_name)
                break
    return EventExtractionResult(draft=result.output, provider=provider)
