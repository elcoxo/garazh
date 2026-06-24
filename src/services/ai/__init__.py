from functools import cache

from models.enums import AIProvider
from services.ai.agent import extract_event
from services.ai.drivers import AbstractAIProvider, GeminiProvider, GroqProvider
from services.ai.requester import AIRequester

__all__ = ['extract_event', 'get_ai_requester']


# LEGACY: ручной failover через AIRequester. Новый код использует extract_event (PydanticAI).
@cache
def get_ai_requester() -> AIRequester:
    providers: dict[AIProvider, AbstractAIProvider] = {
        AIProvider.GEMINI: GeminiProvider(),
        AIProvider.GROQ: GroqProvider(),
    }
    return AIRequester(providers)
