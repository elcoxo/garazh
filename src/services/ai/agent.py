from datetime import date
from functools import cache

from pydantic_ai import Agent
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from sqlalchemy.ext.asyncio import AsyncSession

from models.enums import AIProvider
from services.ai.exceptions import AIDisabledError
from services.ai.priority import get_ai_settings
from services.ai.schemas import EventDraft, EventExtractionResult
from settings import get_settings

cfg = get_settings()

SYSTEM_PROMPT = (
    'Ты извлекаешь события из русскоязычных афиш и анонсов в Telegram. '
    'Заполняй поля строго по описанию каждого Field в схеме EventDraft. '
    'Если в посте несколько событий с разными датами — верни первое по времени. '
    'Если текст не про конкретное событие (новость, реклама, обсуждение, мем) — '
    'верни null вместо объекта.'
)


@cache
def _gemini_model() -> GoogleModel:
    return GoogleModel(cfg.gemini_model, provider=GoogleProvider(api_key=cfg.gemini_api_key))


@cache
def _groq_model() -> GroqModel:
    return GroqModel(cfg.groq_model, provider=GroqProvider(api_key=cfg.groq_api_key))


@cache
def _build_agent(main: AIProvider) -> Agent[None, EventDraft | None]:
    gemini = _gemini_model()
    groq = _groq_model()
    if main == AIProvider.GEMINI:
        model = FallbackModel(gemini, groq)
    else:
        model = FallbackModel(groq, gemini)
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

    result = await _build_agent(settings.main).run(text)
    provider = AIProvider.GEMINI if result.response.provider_name == 'google' else AIProvider.GROQ
    return EventExtractionResult(draft=result.output, provider=provider)
