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
from services.ai.schemas import EventDraft
from settings import get_settings

cfg = get_settings()

SYSTEM_PROMPT = (
    'quak',
)


@cache
def _gemini_model() -> GoogleModel:
    return GoogleModel(cfg.gemini_model, provider=GoogleProvider(api_key=cfg.gemini_api_key))


@cache
def _groq_model() -> GroqModel:
    return GroqModel(cfg.groq_model, provider=GroqProvider(api_key=cfg.groq_api_key))


def _build_agent(main: AIProvider) -> Agent[None, EventDraft | None]:
    gemini = _gemini_model()
    groq = _groq_model()
    if main == AIProvider.GEMINI:
        model = FallbackModel(gemini, groq)
    else:
        model = FallbackModel(groq, gemini)
    return Agent(model, output_type=EventDraft | None, system_prompt=SYSTEM_PROMPT)


async def extract_event(text: str, session: AsyncSession) -> EventDraft | None:
    settings = await get_ai_settings(session)
    if not settings.enabled:
        raise AIDisabledError('AI is disabled in app_settings')

    agent = _build_agent(settings.main)
    result = await agent.run(text)
    return result.output
